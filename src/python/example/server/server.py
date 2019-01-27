import platform
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import grpc
import structlog

from example.book.book_pb2 import Book
from example.book.book_service_pb2 import BookAddRequest, BookAddReply, BookGetRequest, BookGetReply, \
    BookDeleteRequest, BookDeleteReply
from example.book.book_service_pb2_grpc import BookRpcServicer, add_BookRpcServicer_to_server
from utils.logging import init_logging
from utils.printer import print_author, print_address

LOG = structlog.get_logger("gRPC_server")


def run_server():
    server = grpc.server(ThreadPoolExecutor(max_workers=3))

    add_BookRpcServicer_to_server(BookRpc(), server)

    server.add_insecure_port("[::]:5001")
    server.start()

    LOG.info("Server is running...")
    LOG.info("(hit Enter to stop)")

    input("")
    server.stop(100)

    LOG.info("Server shutdown")


class BookRpc(BookRpcServicer):
    state = {}

    def get(self, request: BookGetRequest, context: grpc.ServicerContext) -> Book:
        LOG.info("BookRpc get method", book_id=request.id if hasattr(request, 'id') else None)
        if request.id not in self.state:
            return context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Book with id [{request.id}] does not exists!")

        return BookGetReply(book=self.state[request.id])

    def add(self, request: BookAddRequest, context):
        book: Book = request.book
        book.id = self._generate_id()
        self.state[book.id] = book

        author = print_author(book.author)
        author_address = print_address(book.author.address)
        LOG.info("BookRpc add method", book_id=book.id, book_name=book.name, book_price=book.price, author=author,
                 author_address=author_address)
        return BookAddReply(book=book)

    def delete(self, request: BookDeleteRequest, context):
        LOG.info("BookRpc delete method", book_id=request.id if hasattr(request, 'id') else None)
        if request.id not in self.state:
            return context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"Book with id [{request.id}] does not exists!")
        del self.state[request.id]

        return BookDeleteReply()

    def list(self, request, context):
        LOG.info("BookRpc list method")
        return super().list(request, context)

    @staticmethod
    def _generate_id():
        return random.randint(100, 200)


if __name__ == "__main__":
    init_logging()
    LOG.info(f"Python version: [{platform.python_version()}]")
    run_server()
