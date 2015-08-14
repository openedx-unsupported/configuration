SET FOREIGN_KEY_CHECKS=0;

/*
  Remove all password hashes, even for edx employees
*/

UPDATE auth_user
    set
        password = '!';

UPDATE student_passwordhistory
    set
        password = '!';

/*
  Rewrite all emails to used the SES simulator, simulating success.
  Anonymize other user information. Skip @edx.org accounts
*/

UPDATE auth_user
    set 
        email = concat('success+',cast(id AS CHAR),'@simulator.amazonses.com'),
        username = SUBSTRING(SHA1(CONCAT(username,CAST(id as CHAR))) FROM 1 FOR 30),
        first_name = concat('user-',cast(id AS CHAR)),
        last_name = concat('user-',cast(id AS CHAR)),
        last_login = null,
        date_joined = "1970-01-01 00:00:00"
            where email not like ('%@edx.org');

/*
   There are a handful of email changes requests captured in flight.
*/

UPDATE student_pendingemailchange
    set new_email = concat('success+',cast(user_id AS CHAR),'@simulator.amazonses.com');

/*
   Differs slightly to prevent creating duplicate email records. 
   User id isn't stored here and this email is probably not used for
   sending email, but cannot hurt.
*/

UPDATE student_courseenrollmentallowed
    set email = concat('success+','courseenrollmentallowed_',cast(id AS CHAR),'@simulator.amazonses.com');

/* 
  Set the name to the userid and empty the other fields
  This will also empty user profile data for edx employees
*/

UPDATE auth_userprofile
    set 
        name = concat('user-',cast(id as CHAR)),
        language = "",
        location = "",
        meta = "",
        gender = null,
        mailing_address = null,
        year_of_birth = null,
        level_of_education = null,
        goals = null,
        country = "",
        city = null;

SET FOREIGN_KEY_CHECKS=1;
