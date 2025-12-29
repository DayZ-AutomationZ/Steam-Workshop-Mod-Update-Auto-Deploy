## 🎄 HO HO HO, Server Admins!

Want a **NO-STRESS, anti–PBO-error Christmas**?

🎁 Here’s my **100% FREE & open-source Steam Workshop Mod Update Auto-Deployer** —  
a little Christmas present for **DayZ (and other) server owners**.

### No more:
- Players spamming your Discord while you’re eating turkey 🍗  
- *“Admin?? PBO error 😡”* messages  
- Waking up to broken servers  

### What it does
**AutomationZ** watches your local Steam Workshop mods and **automatically deploys updates** to your server — even while you sleep 😴

**Relax. Eat. Sleep. Let AutomationZ handle the stress.**

---

🎄 **Brought to you by Danny van den Brande**

USE THIS TOOL TOGETHER WITH THE RESTART COMPANION AND ELIMINATE YOUR PBO MISMATCH DOWNTIME FOR 99%!
🔗 **AutomationZ Restart Delay Companion**  
[https://github.com/DayZ-AutomationZ/AutomationZ-Restart-Companion/tree/main](https://github.com/DayZ-AutomationZ/AutomationZ-Restart-Companion/tree/main)


# AutomationZ Mod Update Auto-Deploy [![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/R6R51QD7BU)
[![Automation_Z_Mod_Update_Auto_Deploy_Dashboard.png](https://i.postimg.cc/zGxm7tkV/Automation_Z_Mod_Update_Auto_Deploy_Dashboard.png)](https://postimg.cc/18VY5K2Q)

**AutomationZ Mod Update Auto-Deploy** is a desktop tool designed to automatically detect Steam Workshop mod updates and deploy them to your server — **without manual uploads, late-night restarts, or players being locked out due to outdated mods**.

Originally built for **DayZ**, this tool works just as well for **Arma**, other modded games, VPS servers, server parks, and any workflow where folders need to stay in sync.

---

## Why this tool exists

If you run a modded server, you’ve probably experienced this:

- Steam updates one or more mods
- Your server is still running the old version
- Players get errors (PBO mismatch, version mismatch, can’t join)
- You’re offline, asleep, or not near your PC
- Someone messages: *“Server broken, mods outdated”*

This tool **solves that problem permanently**.

---

## What it does

- Monitors your **local Steam Workshop `@mod` folders**
- Detects **any file change** inside a mod folder
- Automatically deploys the **entire mod folder**
- Supports:
  - **FTP / FTPS** upload to remote (DayZ) Game servers
  - **LOCAL** copy to a local (DayZ) Game folder (server parks, sync tools, etc.)
- Sends optional **Discord notifications**
- Works fully unattended (overnight, while you’re away)

---

## How it works

1. The tool creates a **fingerprint** of each watched mod folder
2. On each scan it checks:
   - File count
   - Total size
   - Latest modification time
3. If anything changes:
   - The mod is marked as updated
   - Deployment is queued
4. After a short cooldown (debounce):
   - The **entire mod folder** is deployed safely

This guarantees your server always receives a **complete, consistent mod state**.

---

## Deployment behavior (important)

### Full folder deployment

**Any detected change triggers a full mod folder deployment.**

This prevents:
- Partial uploads
- Broken PBO states
- Signature mismatches
- Race conditions during Steam updates

Stability always beats micro-optimization.

---

## Keys folder behavior

### `keys/` folder is intentionally skipped

This tool **does NOT deploy server keys**.

**Why:**
- `.bikey` files rarely change
- Uploading keys automatically can overwrite existing keys
- Incorrect keys can lock players out

**Recommended practice:**
- Manage keys manually
- Update keys only when a mod author explicitly changes them

This design avoids accidental server lockouts.

---

## Folder layout explained

AutomationZ does **not guess** your server layout.
You define it once — the tool follows it exactly.

### How paths are built

```
<Profile Root> / <Remote mods base> / <@ModName>
```

---

### Common setups

#### Vanilla DayZ / Nitrado / most hosts

Mods live in:

```
/dayzstandalone/@ModName
```

Settings:

- Profile Root: `/dayzstandalone`
- Remote mods base: *(leave empty)*

Result:

```
/dayzstandalone/@ModName
```

---

#### Custom mods folder

Mods live in:

```
/dayzstandalone/mods/@ModName
```

Settings:

- Profile Root: `/dayzstandalone`
- Remote mods base: `mods`

Result:

```
/dayzstandalone/mods/@ModName
```

---

## FTP vs LOCAL deploy modes

### FTP / FTPS
- Uploads mods directly to a remote server
- Works with VPS, dedicated servers, and most hosts

### LOCAL
- Copies mods to a local folder
- Ideal for server parks, shared storage, or sync pipelines

---

## Safe testing (recommended)

You can safely test the tool without waiting for a real Steam update.

### How to test

1. Open any `@ModName` folder
2. Create a small file, for example:
   ```
   test.txt
   ```
3. Run **Scan Now** or wait for the next scan

### Why this is safe

- DayZ ignores loose files like `.txt`
- Only `.pbo` files are loaded by the engine
- Many mods already include documentation files

---

## Debounce, queueing & bundling

- Cooldown waits until Steam finishes writing files
- Multiple mod updates are queued
- Mods deploy sequentially as one batch
- One Discord summary is sent

This ensures smooth behavior during large update waves.

---

## Discord notifications

Optional notifications:
- Update detected
- Deployment finished
- Deployment failed

Perfect for unattended servers.

---

## Designed for

- DayZ server owners
- Arma server owners
- Modded game servers
- VPS & dedicated servers
- Server parks
- Any folder-based deployment workflow

---

## What this tool does NOT do

- Restart servers
- Control hosting panels
- Upload keys automatically

Restart logic differs per host and is intentionally excluded.

---

## Final notes

- Built from real server-owner experience
- Designed to eliminate late-night emergencies
- Stable, predictable, and safe by default
- Works while you sleep

---

## Overview Screenshots

# Dashboard
Main control screen.
[![Automation_Z_Mod_Update_Auto_Deploy_Dashboard.png](https://i.postimg.cc/zGxm7tkV/Automation_Z_Mod_Update_Auto_Deploy_Dashboard.png)](https://postimg.cc/18VY5K2Q)

# Profiles
Server connection profiles.
[![Automation_Z_Mod_Update_Auto_Deploy_Profiles.png](https://i.postimg.cc/25ysKQHr/Automation_Z_Mod_Update_Auto_Deploy_Profiles.png)](https://postimg.cc/QBLYBTGy)

# Mods
Watched Steam Workshop mods.
[![Automation_Z_Mod_Update_Auto_Deploy_mods.png](https://i.postimg.cc/W4zBHG9s/Automation_Z_Mod_Update_Auto_Deploy_mods.png)](https://postimg.cc/1gx7gqhd)

# Settings
Global configuration.
[![Automation_Z_Mod_Update_Auto_Deploy_settings.png](https://i.postimg.cc/Sxg0dTGX/Automation_Z_Mod_Update_Auto_Deploy_settings.png)](https://postimg.cc/BjPwQCks)

# Discord Notification
[![Automation-Z-Mod-Update-Auto-Deploy-Discord.png](https://i.postimg.cc/4d2jtKPd/Automation-Z-Mod-Update-Auto-Deploy-Discord.png)](https://postimg.cc/FdcPXH25)

## 💡 Usage Tip — Discord + Mobile Control Panel

AutomationZ works especially well when combined with **Discord notifications** and your hosting provider’s **mobile control panel**.

How admins actually use it in practice:

1. A Steam Workshop mod updates
2. AutomationZ detects the update and deploys it
3. A **Discord notification** confirms the upload is finished
4. You open your host’s control panel on your phone
   - e.g. **Nitrado App**, or any host web panel
5. Press **Restart Server**

That’s it.

This works:
- At work
- At home
- While traveling
- While fishing 🎣
- Or even jokingly… space travel with GPS internet 🚀😄

Even if you do nothing:
- Most servers restart every 2–4 hours anyway
- The next scheduled restart will load the updated mods

This turns worst‑case **24‑hour downtime** into **minutes or one restart cycle**, without full automation or loss of control.

AutomationZ keeps the **human in the loop**, while removing the boring waiting part.


## Credits

---
🧩 AutomationZ 
These tools are part of the AutomationZ Admin Toolkit:

- AutomationZ Mod Update Auto Deploy (steam workshop)
- AutomationZ Uploader
- AutomationZ Scheduler
- AutomationZ Server Backup Scheduler
- AutomationZ Server Health
- AutomationZ Config Diff 
- AutomationZ Admin Orchestrator
- AutomationZ Log Cleanup Scheduler
- AutomationZ_Restart_Loop_Guard

Together they form a complete server administration solution.

### 💚 Support the project

AutomationZ tools are built for server owners by a server owner.  
If these tools save you time or help your community, consider supporting development.

☕ Support me [Ko-fi](https://ko-fi.com/dannyvandenbrande) 

Created by **Danny van den Brande** “Built to quietly solve problems, not to impress.”
DayZ AutomationZ [![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/R6R51QD7BU)

## Attribution & Credits

AutomationZ is an open-source project created and maintained by **Danny van den Brande**.

If you fork, modify, or redistribute this project, you **must** retain the original
copyright notice and MIT license, as required by the license.

Visible attribution in the UI or documentation is **appreciated**, but not required.
If you build upon AutomationZ, please consider crediting the original project:

**AutomationZ**  
https://github.com/DayZ-AutomationZ

Thank you for respecting the work and the time behind it.

