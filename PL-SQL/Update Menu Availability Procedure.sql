create or replace procedure update_menu_availability as
begin

    update item_ingredients
    set status = 'unavailable'
    where ingredient_id in (select id from inventory where quantity = 0);

    update menu
    set status = 'unavailable'
    where item_id in (select item_id from item_ingredients where ingredient_id in (select id from inventory where quantity = 0));
    
    dbms_output.put_line('Availability and status updated successfully.');
exception
    when others then
        rollback;
        dbms_output.put_line('an error occurred: ' || sqlerrm);
end update_menu_availability;
/
