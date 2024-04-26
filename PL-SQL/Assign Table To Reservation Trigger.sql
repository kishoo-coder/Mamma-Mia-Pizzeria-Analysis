create or replace trigger assign_table_number
before insert on reservation
for each row
declare
    v_available_table_number seating.table_no%type;
begin
    select table_no into v_available_table_number
    from (
        select table_no, row_number() over (order by table_no) as rn
        from seating
        where available_status = 'true'
        and table_no not in (
            select reservation.table_number 
            from reservation
            where trunc(reservation_date) = trunc(to_date(:new.reservation_date, 'yyyy-mm-dd'))
            and (
                reservation_time = :new.reservation_time or
                reservation_time between :new.reservation_time - interval '90' minute and :new.reservation_time + interval '90' minute
            )
        )
    )
    where rn = 1;

    :new.table_number := v_available_table_number;

    update seating
    set available_status = 'false'
    where table_no = v_available_table_number;

exception
    when no_data_found then
        raise_application_error(-20001, 'no available table for the reservation at the specified time.');
    when others then
        raise_application_error(-20002, 'an error occurred while assigning table.');
end;
