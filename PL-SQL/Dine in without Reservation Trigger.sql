create or replace trigger update_orders_and_seating
before insert or update on orders for each row
declare
    v_reserved_table_no reservation.table_number%type;
    v_next_reservation_exists number;
    v_90_minutes_before timestamp;
    v_90_minutes_after timestamp;
    v_available_table_no number;
    v_order_timestamp timestamp;
begin
    if :new.status = 'dine in without reservation' then
       v_order_timestamp := to_timestamp(to_char(:new.order_date, 'yyyy-mm-dd') || ' ' || to_char(:new.order_time, 'hh24:mi:ss'), 'yyyy-mm-dd hh24:mi:ss');

        v_90_minutes_before := v_order_timestamp - interval '90' minute;
        v_90_minutes_after := v_order_timestamp + interval '90' minute;

        begin
            select table_number
            into v_reserved_table_no
            from reservation
            where reservation_date = trunc(:new.order_date)
            and reservation_time >= v_90_minutes_before
            and reservation_time <= v_90_minutes_after
            and table_number = :new.table_no
            and rownum = 1;
        exception
            when no_data_found then
                v_reserved_table_no := null;
        end;

        if v_reserved_table_no is null then
        
            if :new.table_no is null then
                select table_no
                into v_available_table_no
                from seating
                where party_no >= :new.people
                and available_status = 'true'
                and rownum = 1; 
                
                if v_available_table_no is not null then
                    :new.table_no := v_available_table_no;
                    update seating
                    set available_status = 'false'
                    where table_no = v_available_table_no;
                else
                    raise_application_error(-20001, 'no suitable table available');
                    null; 
                end if;
            end if;
        end if;
    end if;
end;
