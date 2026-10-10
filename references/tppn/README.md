# NYC DOB TPPN archive

The downloader starts at the [official DOB Policy and Procedure Notices page](https://www.nyc.gov/site/buildings/codes/policy-procedure-notices.page) and follows its TPPN archive links.

Official Technical Policy and Procedure Notice PDFs are saved here by the **Download NYC DOB TPPNs** GitHub Actions workflow. `index.json` records original PDF links, the listing pages, SHA-256 checksums and download errors. Existing files remain available if a later download fails.

The workflow runs once when its configuration is pushed to `main`. To run it again, open the repository's **Actions → Download NYC DOB TPPNs → Run workflow**. It commits the downloaded files to `main` and also provides a downloadable ZIP artifact. GitHub Actions must be enabled and the repository must allow its workflow to write repository contents. Branch protection can prevent the commit; the artifact remains downloadable when collection succeeds.

To run on your own computer, from the repository root:

```sh
python scripts/download_tppn.py
```

Only PDFs linked from official TPPN archive pages are collected. Buildings Bulletins are outside this collection. Finding a notice here does not establish that it is still applicable: verify rescission, supersession and current DOB guidance. The PDFs are an archive and are not yet indexed or automatically used by the review app. Original files can be viewed on GitHub or downloaded with the repository ZIP.
