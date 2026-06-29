# Guided install — paste this into Claude Desktop

**New to Claude Code?** If you use the Claude **desktop chat app** (claude.ai) and aren't sure how to install Claude Code and the Time Assistant plugin, copy **everything inside the box below** and paste it as a message to Claude in the desktop app. Claude will walk you through it one step at a time.

> Claude Code is a *separate app* from the chat you're in. This prompt has Claude guide you through getting it, then installing the plugin. (Claude can't click or run things for you in the chat, so it'll give you exact steps and you do them.)

---

```text
You're going to help me install Claude Code and then the "Time Assistant" plugin.
I'm NOT technical. Go ONE STEP AT A TIME: give me a single short, concrete step,
then wait for me to tell you it worked before giving the next step. You can't run
commands or click things for me (this is a chat), so give me exact things to
download/click/type and I'll do them. If something fails, help me troubleshoot
before moving on.

Key facts you need (use them to guide me):

1. Claude Code is a SEPARATE app from this chat window. I need to install it. It
   requires a PAID Claude plan (Pro, Max, Team, or Enterprise) — the free plan does
   NOT include Claude Code. Check with me that I have a paid plan before we start.

2. Download Claude Code for my operating system:
   - macOS:   https://claude.ai/api/desktop/darwin/universal/dmg/latest/redirect
   - Windows: https://claude.com/download
   - Linux / prefer the terminal:  curl -fsSL https://claude.ai/install.sh | bash
   - Official install guide (if anything looks different): https://code.claude.com/docs/en/setup
   On Windows, also have me install "Git for Windows" (it provides the shell Claude Code uses).

3. After installing, I open Claude Code and sign in with my Anthropic account.

4. CRITICAL: the next commands must be run INSIDE a Claude Code session — its
   terminal/`>_` interface — NOT in a normal chat window. If I ever see a message
   like "/plugin isn't available in this environment", I'm in the wrong place:
   tell me to open a Claude Code session first.

5. Then I run these THREE commands, one at a time, in the Claude Code session:
       /plugin marketplace add rimaslogic/time-assistant
       /plugin install time-assistant@rimaslogic-plugins
       /reload-plugins
   The third one (/reload-plugins) activates the freshly installed plugin.

6. Troubleshooting you should proactively watch for:
   - If running `claude` in a terminal says "command not found", the program is
     usually at ~/.local/bin/claude — have me run that full path, or add
     ~/.local/bin to my PATH.
   - If a command says it's "not available in this environment", I'm in a plain
     chat window, not a Claude Code session — guide me to open one.

7. Finally, I type this into the Claude Code session:
       set up my time assistant
   A friendly setup wizard then takes over (it sets up its own Python automatically,
   connects my calendar, etc.) — at that point your job is done.

Start now by asking me: (a) do I have a paid Claude plan, and (b) which operating
system am I on (macOS, Windows, or Linux)? Then guide me from there, one step at a time.
```

---

Once the wizard starts (`set up my time assistant`), follow it in the Claude Code session — see [`INSTALL.md`](../INSTALL.md) for the full reference and troubleshooting.
