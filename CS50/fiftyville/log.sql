-- Keep a log of any SQL queries you execute as you solve the mystery.
SELECT description FROM crime_scene_reports WHERE year = 2021 AND month = 7 AND day = 28 AND street = "Humphrey Street";
-- Theft of the CS50 duck took place at 10:15am at the Humphrey Street bakery. Interviews were conducted today with three witnesses who were present at the time – each of their interview transcripts mentions the bakery.
-- Littering took place at 16:36. No known witnesses

-- witnesses interviews with the witnesses mentions about bakery
SELECT name, transcript
FROM interviews
WHERE year = 2021 AND month = 7 AND day = 28 AND transcript LIKE "%bakery%";

-- sometime within ten minutes of the theft, cars that left on that timeframe
SELECT name FROM people
JOIN bakery_security_logs ON bakery_security_logs.license_plate = people.license_plate
WHERE year = 2021 AND month = 7 AND day = 28 AND hour = 10 AND minute >= 15 AND minute <= 25 AND activity ="exit";
-- suspects Vanessa Bruce Barry Luca Sofia Iman Diana Kelsey

-- I don't know the thief's name, but it was someone I recognized before I arrived at Emma's bakery,
-- I was walking by the ATM on Leggett Street and saw the thief there withdrawing some money.
SELECT name FROM people
JOIN bank_accounts ON bank_accounts.person_id = people.id
JOIN atm_transactions ON atm_transactions.account_number = bank_accounts.account_number
WHERE year = 2021 AND month = 7 AND day = 28 AND atm_location = "Leggett Street" AND transaction_type = "withdraw";
--suspects Bruce Diana Brooke Kenny Iman Luca Taylor Benista

-- suspects on two scenarios Bruce Luca Iman Diana

-- As the thief was leaving the bakery, they called someone who talked to them for less than a minute.
-- In the call, I heard the thief say that they were planning to take the earliest flight out of Fiftyville tomorrow.
-- The thief then asked the person on the other end of the phone to purchase the flight ticket.
SELECT name FROM people
JOIN passengers ON passengers.passport_number = people.passport_number
WHERE passengers.flight_id = (
SELECT id FROM flights
WHERE year = 2021 AND month = 7 AND day = 29 AND
origin_airport_id =(SELECT id FROM airports
WHERE city = 'Fiftyville')
ORDER BY hour, minute);
-- suspect Doris Sofia Bruce Edward Kelsey Taylor Kenny Luca

-- suspects on three scenarios Bruce Luca

- who talk on phone less than a minute that day
SELECT name FROM people
JOIN phone_calls ON phone_calls.caller = people.phone_number
WHERE year = 2021 AND month = 7 AND day = 28 AND duration < 60;
--suspects Sofia  Kelsey Bruce Kelsey Taylor Diana Carina Kenny Benista

--suspect on four scenarios Bruce

SELECT city FROM airports
WHERE id = (SELECT destination_airport_id FROM flights
WHERE year = 2021 AND month = 7 AND day = 29 AND origin_airport_id = (
SELECT id FROM airports WHERE city = 'Fiftyville')
ORDER BY hour, minute);
-- New York City Destination

-- Bruce phone number
SELECT phone_number FROM people WHERE name = "Bruce";
-- (367) 555-5533 number

-- Bruce call that day for a minute or less
SELECT name FROM people WHERE phone_number = (
SELECT receiver FROM phone_calls
WHERE year = 2021 AND month = 7 AND day = 28 AND duration < 60 AND caller = '(367) 555-5533');
-- call receiver robin