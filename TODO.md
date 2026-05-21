# TODO - Shopifyy Flask project

## Completed
- Updated `party.html` product links to call Flask routes via `url_for(..._details)`.
- Updated `ethnic.html` product links to call Flask routes via `url_for(..._details)`.

## Next steps (needed)
- Add missing Flask routes in `flask_project/app.py` for:
  - `elegant_details` (Elegant Evening Gown) -> renders `html_project/elegant.html`
  - `shimmer_details` (Shimmer Party Dress) -> renders `html_project/shimmer.html`
  - `red_details` (Red Satin Party Dress) -> renders `html_project/red.html`
  - `black_details` (Black Sequin Dress) -> renders `html_project/black.html`
  - `anarkali_details` (Anarkali Dress) -> renders `html_project/anarkali.html`
  - `kurti_details` (Kurti Set) -> renders `html_project/kurti.html`
  - `lehenga_details` (Lehenga Choli) -> renders `html_project/lehenga.html`
  - `saree_details` (Saree Collection) -> renders `html_project/saree.html`
- Fix any remaining broken links in `party.html`/`ethnic.html` for paths/route names.
- Run the Flask app and verify clicking each product opens its correct page.
