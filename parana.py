import sqlite3

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