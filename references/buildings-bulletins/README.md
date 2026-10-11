# NYC DOB Buildings Bulletins

The **Download NYC DOB Buildings Bulletins** GitHub workflow saves official PDFs in this folder, with source URLs, listing-page URLs, download dates, sizes and SHA-256 checksums in `index.json`. Download errors are recorded explicitly. Previously downloaded PDFs are preserved when a later source fails.

Discovery starts at the known working [DOB Policy and Procedure Notices page](https://www.nyc.gov/site/buildings/codes/policy-procedure-notices.page), follows its Buildings Bulletins navigation links and year archives, and downloads bulletin PDFs. It does not guess an archive URL. TPPNs remain in their separate collection.

The workflow starts on pushes affecting its configuration or downloader. To run manually, open **Actions → Download NYC DOB Buildings Bulletins → Run workflow → main**. It commits results into this repository and offers a ZIP artifact. Actions must be enabled with repository write permissions; branch protection can prevent direct commits.

Local command, from the repository root:

```sh
python scripts/download_bulletins.py
```

These are reference archives, not verified current requirements. Check each bulletin's applicability, supersession and rescission against DOB's current guidance. They are not yet extracted, indexed or used by the review app.
