"""import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
db = SQL("sqlite:///finance.db")
x=db.execute("SELECT price,symbol,name,shares FROM buy WHERE id=:id", id=1)
print(x)
y=db.execute("DELETE FROM buy WHERE id=:id", id=1)
print(y)
x=db.execute("SELECT price,symbol,name,shares FROM buy WHERE id=:id", id=1)
print(x)"""