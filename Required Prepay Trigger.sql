create or replace trigger update_required_prepay_trigger
before insert or update ON RESERVATION for each row
begin
    if :new.people <= 10 then
        :new.required_prepay := 'true';
    end if;
end;
/
