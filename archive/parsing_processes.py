import time, multiprocessing
from src.parsers.realt_parser_class import RealtParser
from src.parsers.gohome_parser_class import GohomeParser


def parsing_run(page_start=0, page_end=1):
    time_start = time.time()
    gohome_parser = GohomeParser(page_start, page_end)
    realt_parser = RealtParser(page_start, page_end)

    if __name__ == '__main__':
        gohome_process = multiprocessing.Process(target=gohome_parser.update_with_last_flats())
        realt_process = multiprocessing.Process(target=realt_parser.update_with_last_flats())
        gohome_process.start()
        realt_process.start()

        gohome_process.join()
        realt_process.join()

    time_finish = time.time()
    print(time_finish - time_start)

#
parsing_run(3, 4)
