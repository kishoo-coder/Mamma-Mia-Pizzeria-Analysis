create or replace procedure check_item_availability (
    p_item_id in order_items.item_id%type,
    p_availability out varchar2
)
is
    item_status menu.status%type;
begin
    select status 
    into item_status
    from menu
    where item_id = p_item_id;

    if item_status <> 'available' then
        p_availability := 'unavailable';
    else
        p_availability := 'available';
    end if;
end check_item_availability;
/
-----------------
create or replace trigger before_insert_order_items
before insert on ORDER_ITEMS for each row
declare
    v_item_availability varchar2(20);
begin
    check_item_availability(:new.item_id, v_item_availability);

    if v_item_availability = 'unavailable' then
        raise_application_error(-20001, 'the item is unavailable for ordering.');
    end if;
end;
/