# Binding correction: producer-owned directory creation

This addendum supersedes only the `created_at` field, creation ordering, and suggestion that root precreates D in review.md. All other findings and the two-change disposition stand. The producer capsule states that P1 creates its own new exclusive D; do not require incompatible root precreation or an unobserved exact mkdir timestamp.

For the proposed namespace record, replace `created_at` with two required UTC fields:

- `absent_before_launch_at`: actual root/controller observation that D does not exist, before launching P1, while root's namespace ownership is already active.
- `directory_observed_at`: actual root/controller observation of the resulting canonical non-symlink directory and its device/inode after successful producer wait, before sealing.

Require lease.start <= absent_before_launch_at <= publication.launched_at <= publication.wait_observed_at <= directory_observed_at <= manifest.sealed_at <= lease.end. Retain the observations in `evidence`. The adopted producer's exclusive creation during the request-bound invocation supplies the construction contract; root's active sole-writer ownership covers the interval before the post-wait directory observation. Do not assert machine-proven inode continuity before the first actual inode observation or an exact creation timestamp absent a real contemporaneous observation. Recheck that observed inode thereafter at the existing consumer/P4 boundaries.

This is executable with the existing producer and root orchestration: root reserves the unused path and holds scheduling ownership before launch; P1 creates it; root observes it after waiting. No production change, new helper, speculative monitoring service or actual execution is implied. If the required assurance exceeds this explicit human/root trust boundary, custody remains unavailable rather than synthesizing evidence.
