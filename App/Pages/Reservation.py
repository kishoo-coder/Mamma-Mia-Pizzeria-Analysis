import streamlit as st
import cx_Oracle
from datetime import datetime, timedelta
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

def display_results(results):
    try:
        columns = ["Item_ID", "Item_Name", "Item_Size", "Item_Category", "Ingredients", "Price", "Cost", "Status"]
        data = [dict(zip(columns, row)) for row in results]
        df = pd.DataFrame(data)
        col = df.columns.drop('Cost')
        st.dataframe(df[col])
    except:
        st.error("Error:")


def choose_random_number(current_time):
    if time_range1_start <= current_time <= time_range1_end:
        return random.choice([6, 7, 34])
    elif time_range2_start <= current_time or current_time <= time_range2_end:
        return random.choice([5, 8])
    else:
        return None

def get_shift(current_time):
    if time_range1_start <= current_time <= time_range1_end:
        return "Morning"
    elif time_range2_start <= current_time or current_time <= time_range2_end:
        return "Night"
    else:
        return None



def fetch_reservations(selected_date):
    formatted_date = selected_date.strftime("%d/%m/%Y")
    query = f"SELECT * FROM RESERVATION WHERE RESERVATION_DATE = TO_DATE('{formatted_date}', 'DD/MM/YYYY')"
    cursor = connection.cursor()
    cursor.execute(query)
    reservations = cursor.fetchall()
    return reservations

def insert_reservation(name, reservation_date, reservation_time, people, purpose):
    try:
        required_prepay = "TRUE" if people >= 10 else "FALSE"
        formatted_date = reservation_date.strftime("%d-%m-%Y")
        formatted_time = reservation_time.strftime("%I:%M:%S %p")
        cursor = connection.cursor()
        cursor.execute("SELECT Reservation_seq.nextval FROM dual")
        booking_id = cursor.fetchone()[0]
        query = """
        INSERT INTO RESERVATION (BOOKING_ID, NAME, RESERVATION_DATE, RESERVATION_TIME, PEOPLE, REQUIRED_PREPAY, PURPOSE, STATUS_ORDER, TABLE_NUMBER)
        VALUES (:booking_id, :name, TO_DATE(:reservation_date, 'DD-MM-YYYY'), TO_TIMESTAMP(:reservation_time, 'HH:MI:SS PM'), :people, :required_prepay, :purpose, 'Pending', NULL)
        """
        cursor.execute(query, {
            'booking_id': booking_id,
            'name': name,
            'reservation_date': formatted_date,
            'reservation_time': formatted_time,
            'people': people,
            'required_prepay': required_prepay,
            'purpose': purpose
        })
        connection.commit()
        st.success("Reservation added successfully!")
    except:
        st.error(f"Error inserting reservation: : No Tables Found")

def mark_arrived_reservation(name, current_time, current_date):
    try:
        formatted_date = current_date.strftime("%d-%m-%y")
        
        name_check_query = """
        SELECT BOOKING_ID, RESERVATION_TIME, TABLE_NUMBER, PEOPLE
        FROM RESERVATION
        WHERE NAME = :name AND STATUS_ORDER = 'Pending'
        """
        cursor = connection.cursor()
        cursor.execute(name_check_query, {'name': name})
        result = cursor.fetchone()
        
        if not result:
            st.error("No reservation found for the provided name.")
            return None  # Return None if no reservation found
        
        booking_id, reservation_time_str, table_no, people = result
        reservation_time = reservation_time_str
        
        arrival_datetime_str = f"{current_date.strftime('%d-%m-%Y')} {current_time.strftime('%I:%M:%S %p')}"
        arrival_datetime = datetime.strptime(arrival_datetime_str, "%d-%m-%Y %I:%M:%S %p")
        
        start_window = datetime.combine(current_date, reservation_time.time()) - timedelta(hours=1)
        end_window = datetime.combine(current_date, reservation_time.time()) + timedelta(hours=1)
        
        if not (start_window <= arrival_datetime <= end_window):
            st.error("Arrival time should be within 1 hour before or after the reservation time.")
            return None  # Return None if arrival time is not within the window
        
        query = """
        UPDATE RESERVATION
        SET ARRIVAL_TIME = :arrival_time, STATUS_ORDER = 'Ok'
        WHERE BOOKING_ID = :booking_id 
        """
        cursor.execute(query, {'arrival_time': arrival_datetime, 'booking_id': booking_id})
        connection.commit()
        
        st.success("Reservation marked as arrived successfully!")
        return booking_id, table_no, people  # Return the booking_id after successful update

    except:
        st.error(f"Error marking reservation as arrived")
        return None  # Return None in case of any error



random_number = choose_random_number(current_time)
shift = get_shift(current_time)

st.markdown('## 🍕 mamma mia pizzeria system')
st.write('------------')
st.markdown('##### Reservation')


tab3,tab1,tab2 = st.tabs(["Arrived Reservations","Reservation","New Reservation"]) 


with tab1:
    selected_date = st.date_input("Select a date", min_value=None)
    if st.button("Fetch Reservations"):
        reservations = fetch_reservations(selected_date)
        if reservations:
            st.write("Reservations for", selected_date)
            df = pd.DataFrame(reservations, columns=["BOOKING_ID", "NAME", "ORDER_ID", "RESERVATION_DATE", "RESERVATION_TIME", "ARRIVAL_TIME", "PEOPLE", "REQUIRED_PREPAY", "PURPOSE", "STATUS_ORDER", "TABLE_NUMBER"])
            st.write(df)
        else:
            st.write("No reservations found for", selected_date)
with tab2:

    new_name = st.text_input("Name")
    if not new_name:
        st.warning("Please enter a valid name.")
        new_reservation_date = st.date_input("Reservation Date", min_value=datetime.now())
        new_reservation_time = st.time_input("Reservation Time")
        new_people = st.number_input("Number of People", min_value=1, max_value=14)
        new_purpose_options = ["Dinner with Friends", "Sweet Anniversary", "Single Dinner", "Important Date", "Business Dinner", "Anniversary Celebration", "Other", "Family Gathering", "Birthday Celebration"]
        new_purpose = st.selectbox("Purpose", new_purpose_options)
        

    else: 
        new_reservation_date = st.date_input("Reservation Date", min_value=datetime.now())
        new_reservation_time = st.time_input("Reservation Time")
        new_people = st.number_input("Number of People", min_value=1, max_value=14)
        new_purpose_options = ["Dinner with Friends", "Sweet Anniversary", "Single Dinner", "Important Date", "Business Dinner", "Anniversary Celebration", "Other", "Family Gathering", "Birthday Celebration"]
        new_purpose = st.selectbox("Purpose", new_purpose_options)
        if st.button("Add Reservation"):
                insert_reservation(new_name, new_reservation_date, new_reservation_time, new_people, new_purpose)


with tab3:
    arrived_name = st.text_input("Name for Arrived Reservation")
    arrival_time = st.write(f"Arrival Time: {current_time.strftime('%I:%M:%S %p')}")
    if st.button("Mark Arrived"):
        current_date = datetime.now().date()
        current_time = datetime.now().time()
        result = mark_arrived_reservation(arrived_name, current_time, current_date)
        if result:
            booking_id, table_no, people = result
            # Store booking_id, table_no, and people in session state
            st.session_state.booking_id = booking_id
            st.session_state.table_no = table_no
            st.session_state.people = people


    Arrived = st.checkbox("Arrived")
    if Arrived:
        Menu_query = "SELECT * FROM menu"
        cursor, results = execute_query(connection, Menu_query)

        Menu_selectbox = st.selectbox("MENU", ['Hide', 'Show'])
        if Menu_selectbox == 'Show':
            display_results(results)
        st.write('---------')
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
                    l_status = "Dine in with Reservation"
                    l_item_id = item
                    l_quantity = quantity

                    st.session_state.order_items.append((l_item_id, l_quantity))

                    st.success("Order item added successfully!")

                except Exception as e:
                    st.error(f"Error adding order item: {e}")
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
                    INSERT INTO orders (ORDER_ID, ORDER_DATE, ORDER_TIME, ORDER_PRICE, PEOPLE, TABLE_NO, STATUS, SHIFT, EMPLOYEE_ID, KITCHEN_STAFF, ORDER_STATUS)
                    VALUES (:order_id, TO_DATE(:order_date, 'DD-MM-YY'), TO_TIMESTAMP(:order_time, 'HH:MI:SS PM'), :order_price, :people, :table_no, 'Dine in with Reservation', :shift, :random_number, NULL, 'Pending')
                    """

                    cursor.execute(order_query, {
                        'order_id': last_order_id, 
                        'order_date': current_date, 
                        'order_time': current2_time, 
                        'order_price': order_price_result, 
                        'people': st.session_state.people, 
                        'table_no': st.session_state.table_no,
                        'shift': shift, 
                        'random_number': random_number
                    })

                    connection.commit()  
                    st.success("Order completed successfully!")
                    st.session_state.order_items = []
                    query = "UPDATE RESERVATION SET ORDER_ID = :last_order_id WHERE BOOKING_ID = :booking_id"

                    
                    try:
                        cursor.execute(query, {'last_order_id': last_order_id, 'booking_id': st.session_state.booking_id})
                        connection.commit()
                    except cx_Oracle.DatabaseError as e:
                        st.error(f"Error updating reservation with order ID:")
                except Exception as e :
                    st.error(f"Error completing order {e}")
                finally:
                    cursor.close()

