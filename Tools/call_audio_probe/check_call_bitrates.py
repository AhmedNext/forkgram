"""Apply the production overlay and check effective call bitrate configuration.

Run from any directory. Use --patch-ref HEAD to check a committed overlay.
This checks configuration, not the bitrate of an actual phone call.
"""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patch-ref", help="Git revision containing the overlay to check")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    patch_path = "TMessagesProj/jni/soundtouch/patches/tgcalls-audio.patch"
    if args.patch_ref:
        patch = subprocess.check_output(
            ["git", "show", f"{args.patch_ref}:{patch_path}"], cwd=root)
    else:
        patch = (root / patch_path).read_bytes()

    names = ("MediaManager.cpp", "group/GroupInstanceCustomImpl.cpp",
             "v2/InstanceV2Impl.cpp")
    failures = []
    with tempfile.TemporaryDirectory(prefix="telegram-call-codecs-") as directory:
        generated = Path(directory)
        for name in names:
            destination = generated / "tgcalls" / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / "TMessagesProj/jni/tgcalls/tgcalls" / name,
                            destination)
        subprocess.run(
            ["git", "apply", "--unsafe-paths", f"--directory={generated.as_posix()}", "-"],
            input=patch, cwd=root, check=True, capture_output=True)
        for name in names:
            source = (generated / "tgcalls" / name).read_text()
            if name != "v2/InstanceV2Impl.cpp":
                allocation = re.search(
                    r"WebRTC-Audio-Allocation/min:(\d+)kbps,max:(\d+)kbps/", source)
                if not allocation or allocation.groups() != ("32", "128"):
                    failures.append(f"{name}: expected adaptive 32-128 kbps allocation")
                durations = re.findall(r"const uint8_t opusPTimeMs = (\d+);", source)
                if not durations or durations[-1] != "20":
                    failures.append(f"{name}: expected 20 ms outgoing packets")
            encoder_targets = re.findall(
                r"(?:opusCodec|codec)\.SetParam\(cricket::kCodecParamMaxAverageBitrate,\s*(\d+)\)",
                source)
            if encoder_targets != ["128000"]:
                failures.append(f"{name}: expected explicit 128000 bps Opus target")
    if failures:
        raise SystemExit("FAIL:\n" + "\n".join(failures))
    print("PASS: production overlay applies; allocation permits 32-128 kbps; "
          "all three senders explicitly configure Opus at 128000 bps")


if __name__ == "__main__":
    main()
