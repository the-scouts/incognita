from incognita.maps.dashboard import Dashboard

dashboard = Dashboard()

if __name__ == "__main__":
    dashboard.run()
else:
    app = dashboard.app.server
