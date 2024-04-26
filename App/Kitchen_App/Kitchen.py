import streamlit as st
import cx_Oracle
from datetime import datetime, timedelta
import random
import pandas as pd




# Constants
current_time = datetime.now().time()
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

def execute_query(connection, query):
    cursor = connection.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    return cursor, results

def update_order_status(order_id, new_status):
    try:
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE ORDERS
            SET ORDER_STATUS = :status
            WHERE ORDER_ID = :order_id
        """, status=new_status, order_id=order_id)
        connection.commit()
    except cx_Oracle.DatabaseError as e:
        st.error(f"Error updating order status: {e}")


def choose_random_number(current_time):
    if time_range1_start <= current_time <= time_range1_end:
        return random.choice([1,11,12, 17,18,36,38])
    elif time_range2_start <= current_time or current_time <= time_range2_end:
        return random.choice([2,9,10,16,37,39])
    else:
        return None

random_number = choose_random_number(current_time)
# Fetch orders with 'Pending' status
selected_query = """
    SELECT o.ORDER_ID, o.ORDER_DATE, o.ORDER_STATUS
    FROM ORDERS o
    WHERE o.ORDER_STATUS = 'Pending' or o.ORDER_STATUS = 'In Progress'
"""
cursor, results = execute_query(connection, selected_query)




def display_results(results):
    try:
        columns = ['ID', "INGREDIENTS",'CATEGORY' ,'QUANTITY', 'UNIT', 'AVAILABILITY_STATUS', 'SUPPLIER_ID' , 'PRICE_PER_UNIT']
        data = [dict(zip(columns, row)) for row in results]
        df = pd.DataFrame(data)
        col = df.columns[1:-2]
        st.dataframe(df[col])
    except Exception as e:
        st.error("Error:", e)

col1,col2 = st.columns([1, 0.4])
with col1: 
    st.markdown("### 📋 Orders List")
    st.write('------------------')
with col2:
    inventory_query = "select * from inventory where AVAILABILITY_STATUS = 'low'"
    cursor, results2 = execute_query(connection, inventory_query)
    Inventory_selectbox = st.selectbox("Check Low Stock", ['Hide', 'Show'])

    if Inventory_selectbox == 'Show':
        display_results(results2)



# Display orders with checkboxes
for order_id, order_date, order_status in results:
    st.markdown(f"###### Order ID: {order_id}, Status: {order_status}")
        # Fetch items for the current order
    item_query = f"""
        SELECT i.ITEM_ID, i.QUANTITY
        FROM ORDER_ITEMS i
        WHERE i.ORDER_ID = {order_id}
    """
    _, item_results = execute_query(connection, item_query)
    
    # Display items for the current order
    for item_id, quantity in item_results:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.write(f"Item ID: {item_id}")
        with col2:
            st.write(f"Quantity: {quantity}")
    if order_status == "Pending":
    # Checkbox for 'In Progress' status
        in_progress = st.checkbox(f"In Progress", key=f"in_progress_{order_id}")
        

        if in_progress:
            update_order_status(order_id, 'In Progress')
            completed = st.checkbox(f"Completed", key=f"completed_{order_id}")
            if completed:
                update_order_status(order_id, 'Completed')
                if random_number is not None:
                    Kitchen_select = f"update orders set KITCHEN_STAFF = :random_number where order_id = :order_id"
                
                try:
                    cursor = connection.cursor()
                    cursor.execute(Kitchen_select, random_number=random_number, order_id=order_id)
                    connection.commit()
                except cx_Oracle.DatabaseError as e:
                    st.error(f"Error updating kitchen staff: {e}")

    else: 
        completed = st.checkbox(f"Completed", key=f"completed_{order_id}")
        if completed:
            update_order_status(order_id, 'Completed')
            if random_number is not None:
                Kitchen_select = f"update orders set KITCHEN_STAFF = :random_number where order_id = :order_id"
            
            try:
                cursor = connection.cursor()
                cursor.execute(Kitchen_select, random_number=random_number, order_id=order_id)
                connection.commit()
            except cx_Oracle.DatabaseError as e:
                st.error(f"Error updating kitchen staff: {e}")
    st.write('---------------------------------')

