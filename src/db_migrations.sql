alter table flats
    add is_tg_posted boolean default false;

alter table flats
    add is_archive boolean default false;

create table if not exists subscriptions(
    id serial PRIMARY KEY,
    selection_field character varying(15),
    selection_value character varying(500),
    constraint subs_unique unique (selection_field, selection_value)
    );

create table if not exists subscribers(
    id serial PRIMARY KEY,
    tg_id character varying(20),
    sub_id integer,
    foreign key (sub_id) references subscriptions (id),
    constraint subs_tg_unique unique (tg_id, sub_id)
    );