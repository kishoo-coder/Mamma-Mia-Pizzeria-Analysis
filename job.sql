create or replace procedure update_seating_availability AS
begin
    update Seating
    set available_status = 'TRUE';
end;
/

begin
    dbms_scheduler.create_job(
        job_name => 'upd_seat_avail_job',
        job_type => 'PLSQL_BLOCK',
        job_action => 'begin update_seating_availability; end;',
        start_date => systimestamp + interval '1' hour, 
        repeat_interval => 'freq = hourly', 
        enabled => true,
        auto_drop => true
    );
end;
/


