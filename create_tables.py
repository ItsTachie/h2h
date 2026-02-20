from h2h import db,app


# clears all the tables and creates them new 
with app.app_context():
    db.drop_all()
    db.create_all()
    print('tables creates')