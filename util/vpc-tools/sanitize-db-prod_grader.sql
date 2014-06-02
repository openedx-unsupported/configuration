SET FOREIGN_KEY_CHECKS=0;

/*
   Grader has its own django core tables.
*/

UPDATE auth_user
    set 
        email = concat('success+',cast(id AS CHAR),'@simulator.amazonses.com'),
        username = concat('user-',cast(id AS CHAR)),
        first_name = concat('user-',cast(id AS CHAR)),
        last_name = concat('user-',cast(id AS CHAR)),
        password = null,
        last_login = null,
        date_joined = null
            where email not like ('%@edx.org');

SET FOREIGN_KEY_CHECKS=1;
