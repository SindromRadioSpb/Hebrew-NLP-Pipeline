# 9.3. FAQ — KADIMA

## Q: Какие форматы поддерживаются?
A: Import: .txt, .csv, .conllu, .json. Export: .csv, .json, .tbx, .tmx

## Q: Какой язык поддерживается?
A: v1.0 — только иврит. v1.x — + арабский.

## Q: Могу ли я добавить свой профиль extraction?
A: Да, через config.yaml. Задайте thresholds для PMI, LLR, freq.

## Q: Как работает validation?
A: Импортируйте gold corpus (manifest + expected CSV), запустите pipeline, система сравнит output с expected.

## Q: Pipeline crashed. Что делать?
A: Посмотрите лог в ~/.kadima/logs/. Ошибка покажет, на каком файле/токене произошёл сбой.

## Q: Как работать с большими корпусами (>100MB)?
A: Разбейте на части (<50MB каждая), обработайте отдельно, затем объедините результаты.

## Q: Можно ли запустить из командной строки?
A: Да: `kadima run --corpus my_corpus --profile balanced --export results.csv`
