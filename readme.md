
## detect gender
guess-gender/guess-gender.py - breaks name into first / last, guesses gender

    CREATE VIEW stats1 AS SELECT gender, count(*) as countx from 'Candidati Alegeri RO' group by gender;
    CREATE VIEW stats2 AS  SELECT [Cod partid], gender, count(*) as countx from 'Candidati Alegeri RO' group by gender, [Cod partid];

see also: [pax/ro-gender-assumer](https://github.com/pax/ro-gender-assumer) 