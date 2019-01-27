import platform

import grpc
import structlog

from utils.logging import init_logging
from example.author.address_pb2 import Address
from example.author.author_pb2 import Author
from example.book.book_pb2 import Book
from example.book.book_service_pb2 import BookAddRequest, BookAddReply, BookGetRequest, BookDeleteRequest
from example.book.book_service_pb2_grpc import BookRpcStub
from utils.printer import print_author, print_address

LOG = structlog.get_logger("gRPC_client")


def wait_for_keyboard(text):
    input(text)


def run_client(book_rpc: BookRpcStub):
    added_id = add_book(book_rpc)
    retrieve_book(book_rpc, added_id)

    delete_book(book_rpc, added_id)
    retrieve_book(book_rpc, added_id)

    wait_for_keyboard("Finish")


def add_book(book_rpc):
    wait_for_keyboard("Add book")
    LOG.debug("Adding book")
    try:
        book_add_reply: BookAddReply = book_rpc.add(BookAddRequest(book=create_book()))
    except grpc.RpcError as error:
        LOG.warn(f"gRPC request failed", code=str(error.code()), details=error.details())
        return None
    else:
        added=book_add_reply.book

        LOG.info(f"Book added", book_id=added.id, book_name=added.name)
        return added.id


def retrieve_book(book_rpc, book_id):
    wait_for_keyboard("Retrieve book")
    LOG.debug("Retriving book", book_id=book_id)
    try:
        book_get_reply = book_rpc.get(BookGetRequest(id=book_id))
    except grpc.RpcError as error:
        LOG.warn(f"gRPC request failed", code=str(error.code()), details=error.details())
    else:
        retrieved = book_get_reply.book

        author = print_author(retrieved.author)
        author_address = print_address(retrieved.author.address)
        LOG.info("Retrived book", book_id=retrieved.id, book_name=retrieved.name, book_price=retrieved.price,
                 author=author, author_address=author_address)


def delete_book(book_rpc, book_id):
    wait_for_keyboard("Delete book")
    LOG.debug("Deleting book", book_id=book_id)
    try:
        book_rpc.delete(BookDeleteRequest(id=book_id))
    except grpc.RpcError as error:
        LOG.warn(f"gRPC request failed", code=str(error.code()), details=error.details())
    else:
        LOG.info("Deleted book")


def create_book():
    address = Address(city="Kraków", street="ul. Zabłocie", number="43a", zip_code="30-123")
    author = Author(first_name="Adam", last_name="Jlabser", address=address)
    book = Book(name="Advanced Python", price="€24.99", author=author)
    return book


if __name__ == "__main__":
    init_logging()
    LOG.info(f"Python version: [{platform.python_version()}]")
    LOG.info("Client is running")
    LOG.info("")

    with grpc.insecure_channel("localhost:5001") as channel:
        run_client(BookRpcStub(channel))
