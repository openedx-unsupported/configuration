SET FOREIGN_KEY_CHECKS=0;

/* 
  Truncate the courseware_studentmodulehistory table since
  it is only needed for analytics    
*/

TRUNCATE courseware_studentmodulehistory;

/*
  Rewrite all emails to used the SES simulator, simulating success.
  Anonymize other user information
*/

UPDATE wwc.auth_user
    set email = concat('success+',cast(id AS CHAR),'@simulator.amazonses.com')
        where email not like ('%@edx.org'),
    set username = concat('user-',cast(id AS CHAR)
        where email not like ('%@edx.org'),
    set first_name = concat('user-',cast(id AS CHAR)
        where email not like ('%@edx.org'),
    set last_name = concat('user-',cast(id AS CHAR)
        where email not like ('%@edx.org'),
    set password = null
        where email not like ('%@edx.org'),
    set last_login = null
        where email not like ('%@edx.org'),
    set date_joined = null
        where email not like ('%@edx.org');

/*
   There are a handful of email changes requests captured in flight.
*/

UPDATE wwc.student_pendingemailchange
    set new_email = concat('success+',cast(user_id AS CHAR),'@simulator.amazonses.com');

/*
   Differs slightly to prevent creating duplicate email records. 
   User id isn't stored here and this email is probably not used for
   sending email, but cannot hurt.
*/

UPDATE wwc.student_courseenrollmentallowed
    set email = concat('success+','courseenrollmentallowed_',cast(id AS CHAR),'@simulator.amazonses.com');

/* 
  Set the name to the userid and empty the other fields
  This will also empty user profile data for edx employees
*/

UPDATE wwc.auth_userprofile
    set name = concat('user-',cast(id as CHAR)),
    set language = "",
    set location = "",
    set meta = "",
    set gender = null,
    set mailing_address = null,
    set year_of_birth = null,
    set level_of_education = null,
    set goals = null
    set country = "",
    set city = null;

/*
   Grader has its own django core tables.
*/

UPDATE prod_grader.auth_user
    set email = concat('success+',cast(id AS CHAR),'@simulator.amazonses.com')
        where email not like ('%@edx.org'),
    set username = concat('user-',cast(id AS CHAR)
        where email not like ('%@edx.org'),
    set first_name = concat('user-',cast(id AS CHAR)
        where email not like ('%@edx.org'),
    set last_name = concat('user-',cast(id AS CHAR)
        where email not like ('%@edx.org'),
    set password = null
        where email not like ('%@edx.org'),
    set last_login = null
        where email not like ('%@edx.org'),
    set date_joined = null
        where email not like ('%@edx.org');


SET FOREIGN_KEY_CHECKS=1;
