def __main__():
    from forums_scraper import ForumsScraper

    fs = ForumsScraper()
    fs.run_process()
    fs = None
