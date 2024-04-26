import streamlit as st
import cx_Oracle
from datetime import datetime , timedelta
import random
import pandas as pd


# Constants
current_time = datetime.now().time()
current_datetime = datetime.now()
current_date = current_datetime.strftime("%d-%m-%y")
current2_time = current_datetime.strftime("%I:%M:%S %p")

time_range1_start = datetime.strptime('09:00:00', '%H:%M:%S').time()
time_range1_end = datetime.strptime('17:00:00', '%H:%M:%S').time()
time_range2_start = datetime.strptime('17:00:00', '%H:%M:%S').time()
time_range2_end = datetime.strptime('00:00:00', '%H:%M:%S').time()


# Connect to Oracle database
try:
    connection = cx_Oracle.connect("GP", "123", "localhost:1521/xe")
except cx_Oracle.DatabaseError as e:
    st.error(f"Error connecting to database: {e}")
    st.stop()

# Function to execute queries
def execute_query(connection, query):
    cursor = connection.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    return cursor, results

# Choose random number based on current time
def choose_random_number(current_time):
    if time_range1_start <= current_time <= time_range1_end:
        return random.choice([6, 7, 34])
    elif time_range2_start <= current_time or current_time <= time_range2_end:
        return random.choice([5, 8])
    else:
        return None

# Determine shift based on current time
def get_shift(current_time):
    if time_range1_start <= current_time <= time_range1_end:
        return "Morning"
    elif time_range2_start <= current_time or current_time <= time_range2_end:
        return "Night"
    else:
        return None
# Generate a random number based on the current time and store it in a variable
random_number = choose_random_number(current_time)
shift = get_shift(current_time)



def display_results(results):
    try:
        columns = ["Item_ID", "Item_Name", "Item_Size", "Item_Category", "Ingredients", "Price", "Cost", "Status"]
        data = [dict(zip(columns, row)) for row in results]
        df = pd.DataFrame(data)
        col = df.columns.drop('Cost')
        st.dataframe(df[col])
    except:
        st.error("Error:")


st.markdown('## 🍕 mamma mia pizzeria system')
st.write('------------')
Menu_query = "SELECT * FROM menu"
cursor, results = execute_query(connection, Menu_query)

Menu_selectbox = st.selectbox("MENU", ['Hide', 'Show'])
if Menu_selectbox == 'Show':
    display_results(results)
st.write('---------')



#with tab1:
col1 , col2  = st.columns(2)
with col2:
        Category_Radio_take_away = st.radio('Choose Category', ["Pizza", "Pasta", "Drink", "Appetizer", "Dessert", "Extra"])

with col1:
    if Category_Radio_take_away:
        query_map = {
            "Pizza": "SELECT item_id FROM Menu WHERE Item_Category='Pizza'",
            "Pasta": "SELECT item_id FROM Menu WHERE Item_Category='Pasta'",
            "Drink": "SELECT item_id FROM Menu WHERE Item_Category='Drink'",
            "Appetizer": "SELECT item_id FROM Menu WHERE Item_Category='Appetizer'",
            "Dessert": "SELECT item_id FROM Menu WHERE Item_Category='Dessert'",
            "Extra": "SELECT item_id FROM Menu WHERE Item_Category='Extra'"
        }
        Pizza_query = query_map.get(Category_Radio_take_away, "")

        cursor, results = execute_query(connection, Pizza_query)
        item_ids = [result[0] for result in results]
        item = st.selectbox("Select Item", item_ids)
        quantity = st.number_input('Quantity', 1, 100)


if 'order_items' not in st.session_state:
    st.session_state.order_items = []
col3 , col4 = st.columns(2)
with col3:
    if st.button("Insert Order Item"):
        try:
            l_status = "take away"
            l_item_id = item
            l_quantity = quantity

            st.session_state.order_items.append((l_item_id, l_quantity))

            st.success("Order item added successfully!")

        except:
            st.error(f"Error adding order item")
with col4:

    if st.button("Order Completed"):
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT order_seq.nextval FROM dual")
            last_order_id = cursor.fetchone()[0]
            
            if not st.session_state.order_items:
                st.error("No order items to insert. Please add order items before completing the order.")
            
            for order_item in st.session_state.order_items:
                l_item_id, l_quantity = order_item
                price_query = 'SELECT price FROM menu WHERE item_id = :item_id'
                cursor.execute(price_query, item_id=l_item_id)
                price_result = cursor.fetchone()[0]
                Total_price = price_result * l_quantity
                
                items_query = """
                INSERT INTO order_items (order_id, item_id, quantity, price, Total_price, customer_rate)
                VALUES (:order_id, :item_id, :quantity, :price, :Total_price, :random_number)
                """

                cursor.execute(items_query, {'order_id': last_order_id, 'item_id': l_item_id, 'quantity': l_quantity, 'price': price_result , 'Total_price':Total_price , 'random_number':random.choice([1,2,3,4,5])})
            
            order_price_query = 'SELECT sum(Total_price) FROM order_items WHERE order_id = :order_id'
            cursor.execute(order_price_query, order_id=last_order_id)
            order_price_result = cursor.fetchone()[0]
            
            order_query = """
            INSERT INTO orders (ORDER_ID, ORDER_DATE, ORDER_TIME, ORDER_PRICE, PEOPLE, TABLE_NO, STATUS, SHIFT, EMPLOYEE_ID, KITCHEN_STAFF , ORDER_STATUS)
            VALUES (:order_id, TO_DATE(:current_date, 'DD-MM-YY'), TO_TIMESTAMP(:current_time, 'HH:MI:SS PM'), :order_price_result, NULL, NULL, 'Take away', :shift, :random_number, NULL ,'Pending')
            """
            
            cursor.execute(order_query, {'order_id': last_order_id, 'current_date': current_date, 'current_time': current2_time, 'order_price_result': order_price_result, 'random_number': random_number , 'shift':shift})
            connection.commit()  
            st.success("Order completed successfully!")
            st.session_state.order_items = []
        except:
            st.error(f"Error completing order: Unavailable item")
        finally:
            cursor.close()
