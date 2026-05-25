import sqlite3

# Helper function to display a numbered list and return the selected id
def _display_options(all_options, title, type):
    option_num = 1
    option_list = []
    print("\n", title, "\n")
    for option in all_options:
        code = option[0]
        desc = option[1]
        print("{0}.\t{1}".format(option_num, desc))
        option_num = option_num + 1
        option_list.append(code)
    selected_option = 0
    while selected_option > len(option_list) or selected_option == 0:
        prompt = "Enter the number against the " + type + " you want to choose: "
        selected_option = int(input(prompt))
    return option_list[selected_option - 1]

# Connect to the database
conn = sqlite3.connect('parana.db')
cursor = conn.cursor()

# Ask user for their shopper ID
shopper_id = int(input("Please enter your shopper ID: "))

# Check if the shopper exists in the database
cursor.execute("SELECT shopper_first_name, shopper_surname FROM shoppers WHERE shopper_id = ?", (shopper_id,))
shopper = cursor.fetchone()

# If found, welcome them. If not, exit.
if shopper:
    print(f"Welcome, {shopper[0]} {shopper[1]}!")
else:
    print("Shopper ID not found. Exiting program.")
    exit()

# Check if shopper has a basket created today
cursor.execute("""
    SELECT basket_id
    FROM shopper_baskets
    WHERE shopper_id = ?
    AND DATE(basket_created_date_time) = DATE('now')
    ORDER BY basket_created_date_time DESC
    LIMIT 1
""", (shopper_id,))

basket = cursor.fetchone()

if basket:
    basket_id = basket[0]
    print("Welcome back! Resuming your basket from today.")
else:
    basket_id = None

# Display the main menu
while True:
    print("\n")
    print("PARANÁ – SHOPPER MAIN MENU")
    print("1. Display your order history")
    print("2. Add an item to your basket")
    print("3. View your basket")
    print("4. Change the quantity of an item in your basket")
    print("5. Remove an item from your basket")
    print("6. Checkout")
    print("7. Exit")
    print("\n")

    choice = int(input("Please enter your choice: "))

    if choice == 7:
        print("Thank you for shopping with Paraná. Goodbye!")
        break

    elif choice == 1:
        # Option 1 - Display order history
        cursor.execute("""
            SELECT so.order_id,
                   strftime('%d-%m-%Y', so.order_date),
                   p.product_description,
                   se.seller_name,
                   '£' || printf('%.2f', op.price),
                   op.quantity,
                   op.ordered_product_status
            FROM shopper_orders so
            JOIN ordered_products op ON so.order_id = op.order_id
            JOIN products p ON op.product_id = p.product_id
            JOIN sellers se ON op.seller_id = se.seller_id
            WHERE so.shopper_id = ?
            ORDER BY so.order_date DESC
        """, (shopper_id,))

        orders = cursor.fetchall()

        if not orders:
            print("No orders placed by this customer")
        else:
            print("\nORDER HISTORY")
            print("-" * 80)
            for row in orders:
                print(f"Order ID: {row[0]}  Date: {row[1]}")
                print(f"  Product: {row[2]}")
                print(f"  Seller: {row[3]}  Price: {row[4]}  Qty: {row[5]}  Status: {row[6]}")
                print("-" * 80)

    elif choice == 2:
        # Option 2 - Add an item to your basket

        # Step 1 - Display categories in alphabetical order
        cursor.execute("SELECT category_id, category_description FROM categories ORDER BY category_description ASC")
        categories = cursor.fetchall()
        category_id = _display_options(categories, "PRODUCT CATEGORIES", "category")

        # Step 2 - Display products in the selected category
        cursor.execute("""
            SELECT product_id, product_description
            FROM products
            WHERE category_id = ?
            ORDER BY product_description ASC
        """, (category_id,))
        products = cursor.fetchall()
        product_id = _display_options(products, "PRODUCTS", "product")

        # Step 3 - Display sellers for the selected product
        cursor.execute("""
            SELECT s.seller_id, s.seller_name || ' - £' || printf('%.2f', ps.price)
            FROM sellers s
            JOIN product_sellers ps ON s.seller_id = ps.seller_id
            WHERE ps.product_id = ?
            ORDER BY s.seller_name ASC
        """, (product_id,))
        sellers = cursor.fetchall()
        seller_id = _display_options(sellers, "SELLERS", "seller")

        # Step 4 - Get quantity from user
        quantity = 0
        while quantity <= 0:
            quantity = int(input("Enter the quantity you want to order: "))
            if quantity <= 0:
                print("The quantity must be greater than 0")

        # Step 5 - Get the price for the selected product and seller
        cursor.execute("""
            SELECT price FROM product_sellers
            WHERE product_id = ? AND seller_id = ?
        """, (product_id, seller_id))
        price = cursor.fetchone()[0]

        # Step 6 - Create a new basket if one doesn't exist
        if basket_id is None:
            cursor.execute("SELECT seq FROM sqlite_sequence WHERE name = 'shopper_baskets'")
            last_id = cursor.fetchone()[0]
            basket_id = last_id + 1
            cursor.execute("""
                INSERT INTO shopper_baskets (basket_id, shopper_id, basket_created_date_time)
                VALUES (?, ?, datetime('now'))
            """, (basket_id, shopper_id))

        # Step 7 - Insert item into basket contents
        cursor.execute("""
            INSERT INTO basket_contents (basket_id, product_id, seller_id, quantity, price)
            VALUES (?, ?, ?, ?, ?)
        """, (basket_id, product_id, seller_id, quantity, price))

        conn.commit()
        print("Item added to your basket!")

    elif choice == 3:
        # Option 3 - View your basket
        if basket_id is None:
            print("Your basket is empty")
        else:
            cursor.execute("""
                SELECT bc.rowid, p.product_description, s.seller_name,
                       bc.quantity, bc.price, (bc.quantity * bc.price)
                FROM basket_contents bc
                JOIN products p ON bc.product_id = p.product_id
                JOIN sellers s ON bc.seller_id = s.seller_id
                WHERE bc.basket_id = ?
            """, (basket_id,))

            items = cursor.fetchall()

            if not items:
                print("Your basket is empty")
            else:
                print("\nYOUR BASKET")
                print("-" * 80)
                total = 0
                item_num = 1
                for item in items:
                    print(f"{item_num}. {item[1]}")
                    print(f"   Seller: {item[2]}  Qty: {item[3]}  Price: £{item[4]:.2f}  Subtotal: £{item[5]:.2f}")
                    total += item[5]
                    item_num += 1
                print("-" * 80)
                print(f"TOTAL: £{total:.2f}")

    elif choice == 4:
        # Option 4 - Change the quantity of an item in your basket
        if basket_id is None:
            print("Your basket is empty")
        else:
            cursor.execute("""
                SELECT bc.rowid, p.product_description, s.seller_name,
                       bc.quantity, bc.price, (bc.quantity * bc.price)
                FROM basket_contents bc
                JOIN products p ON bc.product_id = p.product_id
                JOIN sellers s ON bc.seller_id = s.seller_id
                WHERE bc.basket_id = ?
            """, (basket_id,))

            items = cursor.fetchall()

            if not items:
                print("Your basket is empty")
            else:
                # Display the basket
                print("\nYOUR BASKET")
                print("-" * 80)
                total = 0
                item_num = 1
                for item in items:
                    print(f"{item_num}. {item[1]}")
                    print(f"   Seller: {item[2]}  Qty: {item[3]}  Price: £{item[4]:.2f}  Subtotal: £{item[5]:.2f}")
                    total += item[5]
                    item_num += 1
                print("-" * 80)
                print(f"TOTAL: £{total:.2f}")

                # If more than one item ask which one to update
                if len(items) > 1:
                    basket_item_no = 0
                    while basket_item_no < 1 or basket_item_no > len(items):
                        basket_item_no = int(input("\nEnter the basket item no. you want to update: "))
                        if basket_item_no < 1 or basket_item_no > len(items):
                            print("The basket item no. you have entered is invalid")
                else:
                    basket_item_no = 1

                # Get the rowid of the selected item
                selected_rowid = items[basket_item_no - 1][0]

                # Get new quantity
                new_quantity = 0
                while new_quantity <= 0:
                    new_quantity = int(input("Enter the new quantity: "))
                    if new_quantity <= 0:
                        print("The quantity must be greater than 0")

                # Update the basket
                cursor.execute("""
                    UPDATE basket_contents
                    SET quantity = ?
                    WHERE rowid = ?
                """, (new_quantity, selected_rowid))

                conn.commit()

                # Display updated basket
                cursor.execute("""
                    SELECT bc.rowid, p.product_description, s.seller_name,
                           bc.quantity, bc.price, (bc.quantity * bc.price)
                    FROM basket_contents bc
                    JOIN products p ON bc.product_id = p.product_id
                    JOIN sellers s ON bc.seller_id = s.seller_id
                    WHERE bc.basket_id = ?
                """, (basket_id,))

                updated_items = cursor.fetchall()
                print("\nUPDATED BASKET")
                print("-" * 80)
                total = 0
                item_num = 1
                for item in updated_items:
                    print(f"{item_num}. {item[1]}")
                    print(f"   Seller: {item[2]}  Qty: {item[3]}  Price: £{item[4]:.2f}  Subtotal: £{item[5]:.2f}")
                    total += item[5]
                    item_num += 1
                print("-" * 80)
                print(f"TOTAL: £{total:.2f}")