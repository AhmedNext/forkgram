# Mirrored selfie video in calls

Front-camera video is mirrored in `VideoCapturerDevice` before it enters the
native call source. The transmitted image and the local preview therefore use
the same mirror-style orientation. This applies to private and group calls.

The texture reflection accounts for the frame's display rotation: it flips the
buffer horizontally at 0/180 degrees and vertically at 90/270 degrees, producing
a horizontal reflection in the upright image. Rotation, timestamp, resolution
and the original buffer remain intact. The derived frame is released after the
native observer callback, following WebRTC's buffer ownership rules.

The local main, picture-in-picture, group-call and camera-preview renderers no
longer apply an additional mirror, which would undo the transmitted reflection.
Camera-opening callbacks update which physical camera is active before its
frames arrive. Camera2 and explicitly texture-based Camera1 capture are covered.

Rear-camera video and screen sharing retain their original capture paths. This
change does not modify circle-video notes or audio processing.

Validation: the actual callback's transform factors were checked against the
upright horizontal-reflection property for all four display rotations. Source
checks confirmed the rear-camera/screen-sharing bypasses and removal of extra
preview mirroring. Whitespace checks passed. An Android build and real-device
call test remain necessary; Java and the Android SDK are unavailable locally.
