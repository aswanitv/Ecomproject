# TODO - Seller product dropdown + seller dashboard add (option 1)

- [ ] Inspect and map the hardcoded products from:
  - [ ] flask_project/templates/casual.html
  - [ ] flask_project/templates/party.html
  - [ ] flask_project/templates/ethnic.html
- [x] Update DB schema in `flask_project/app.py`:
  - [x] Add `description` column to `products` table
- [x] Add new Flask route in `flask_project/app.py`:
  - [x] `POST /seller/add_product` to insert a product for current logged-in seller
- [x] Update `flask_project/templates/seller.html`:
  - [x] Add navbar dropdown "Products" that lists product name, price, description
  - [x] Add "Add" buttons that submit to `/seller/add_product`
- [x] Update `flask_project/templates/seller_dashboard.html`:
  - [x] Display product description under each product card
- [ ] Quick verification:
  - [ ] Login as seller
  - [ ] Use navbar "Products" dropdown and click Add
  - [ ] Confirm added products appear in Seller Dashboard with description
