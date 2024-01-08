from app import config, app, socketio, celery

if __name__ == "__main__":
    app.app_context().push()
    # print(config.HOST, config.PORT, config.DEBUG)
    # socketio.run(app, 
    #             host=config.HOST,
    #             port=config.PORT,
    #             debug=config.DEBUG)
