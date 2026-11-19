# Publishing UI Alert Macro v5.3 using GitHub Desktop

1. **Keep your existing GitHub repository.** You can rename it later, but this is not required for v5.3.
2. In GitHub Desktop, open your local clone of `Kizmum/UI_Alert_Macro_v5.2`. Copy the **contents** of the `UI_Alert_Macro_v5_3/` folder into the repository root, overwriting the old `.py`, README, batch files and `ui/` assets. Also add `legacy_ui/`, `CHANGELOG.md`, `GITHUB_RELEASE_GUIDE.md`, and `tests/`. Keep the existing `.git` folder; do **not** paste the outer folder as another repository directory.
3. Inspect **Changes**. Verify that `app_config.json`, private VIP links, real webhook URLs, and any private EX files are absent. `.gitignore` helps but does not replace manual review.
4. Write the commit message `Release v5.3 - TGSS adaptive and legacy detection`. Click **Commit to main**, then **Push origin**.
5. On the repository website open **Releases > Draft a new release**. Choose a new tag `v5.3` and attach the public `UI_Alert_Macro_v5_3.zip` archive. Publish it (or choose **Pre-release** until you have tested a real TGSS event).
6. The old `v5.2` release remains downloadable **if you created its tag/release separately**. Replacing the main branch does not erase the older Git commit history, but the most convenient download is from Releases.

**Important:** `UI_Alert_Macro_v5_3_EX.zip` is the private experiment and must **not** be copied into the public repository or attached to public Releases.
