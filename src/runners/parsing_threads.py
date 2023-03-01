import threading, time
from src.parsers.realt_parser_class import RealtParser
from src.parsers.gohome_parser_class import GohomeParser



def parsing_run(page_start=0, page_end=1):
    time_start = time.time()
    gohome_parser = GohomeParser(page_start, page_end)
    realt_parser = RealtParser(page_start, page_end)
    gohome_thread = threading.Thread(target=gohome_parser.update_with_last_flats)
    realt_thread = threading.Thread(target=realt_parser.update_with_last_flats)
    gohome_thread.start()
    realt_thread.start()

    gohome_thread.join()
    realt_thread.join()

    time_finish = time.time()
    print(time_finish - time_start)


def test(page_start=1, page_end=2):
    time_start = time.time()
    gohome_parser = GohomeParser(page_start, page_end)
    gohome_parser.update_with_last_flats()
    # realt_parser = RealtParser(page_start, page_end)
    # realt_parser.update_with_last_flats()
    time_finish = time.time()
    print(time_finish - time_start)


# #
parsing_run(4,5)
# test()

