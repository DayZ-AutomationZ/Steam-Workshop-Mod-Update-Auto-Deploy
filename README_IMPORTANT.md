# AutomationZ Mod Update Auto-Deploy — Important Notes

This document exists to eliminate the **last 1% of confusion**.  
If you read this, you will not need to ask questions.

---

## 1. First Run Behavior (This Is Normal)

**Q:** Why did all my mods upload on the first run?  
**A:** Because there is no previous state yet.

On first launch, AutomationZ:
- Scans all enabled mods
- Creates a baseline fingerprint
- Treats everything as "new"

This is **expected behavior**.

---

## 2. Does It Upload Only Changed Files?

**Short answer:** No.  
**Correct answer:** It uploads the **entire mod folder** once a change is detected.

### Why?
- DayZ mods rely on consistent PBO states
- Partial uploads can break mods
- Full-folder deploys are safer and predictable

This is **by design**, not a limitation.

---

## 3. Safe Testing (Yes, You Can Test It)

You can safely test the tool by:
- Opening a mod folder
- Creating a small `.txt` file
- Saving it

DayZ **ignores extra files** like:
- `.txt`
- `README.md`
- documentation files

Many real mods already include readmes.

✔ 100% safe  
✔ No impact on gameplay  
✔ Perfect for testing

---

## 4. Why Is the `keys/` Folder Not Uploaded?

This is intentional.

- Server keys are usually managed separately
- Re-uploading keys every update is unnecessary
- Avoids accidental key conflicts

If your host requires keys elsewhere, manage them manually.

---

## 5. Remote Path — The Most Common Mistake

### Your server layout decides this.

#### Example A — Mods live in `/dayzstandalone`
```
@MyMod
```

#### Example B — Mods live in `/dayzstandalone/mods`
```
mods/@MyMod
```

The **Remote Mods Base Folder** simply prepends this path.

There is no "right" or "wrong" — only **your layout**.

---

## 6. Will This Break a Running Server?

No.

But:
- Players may need to reconnect
- Some hosts require a restart to load new PBOs

AutomationZ updates files safely — it does not force restarts.

---

## 7. Why Didn’t It Detect an Update Instantly?

Two reasons:

1. **Scan interval (`tick_seconds`)**
2. **Debounce protection**

Steam writes files in stages.  
AutomationZ waits until files stabilize before deploying.

This prevents:
- Half-written uploads
- Corrupted mods
- Spam deployments

---

## 8. Is This DayZ-Only?

No.

This tool works for:
- Any Steam Workshop game
- Any folder-based mod system
- VPS deployments
- Server parks
- Web assets
- Any automated folder sync use-case

DayZ is just the reason it was created.

---

## 9. Why Are Mods Uploaded Sequentially?

Because safety > speed.

Sequential deploys:
- Prevent FTP overload
- Keep logs readable
- Avoid mixed mod states

This is intentional.

---

## 10. Does This Replace My Hosting Panel?

It replaces **waiting**, not your panel.

Hosting panels are reactive.  
AutomationZ is proactive.

It fixes the problem **before** players complain.

---

## Final Note

If you reached this point and still have questions:

> Read it again. Slowly.

This tool was built so server owners can **sleep**.

Time is the only resource that matters.
