from time import sleep
from typing import Optional

from serializer_utils.deserializer import Deserializable
from serializer_utils.annotations import abstract, discriminate


@abstract
class ReceiptLine(Deserializable):
    pk: Optional[int]
    name: str
    t = 0

    def __repr__(self):
        return 'ReceiptLine(pk={}, name={}, t={})'\
            .format(self.pk, self.name, self.t)


@discriminate('type', 'transaction')
class TransactionLine(ReceiptLine):
    article_id: int
    amount: int

    def __repr__(self):
        return 'TransactionLine(super={}, article_id={}, amount={})'\
            .format(super(TransactionLine, self).__repr__(), self.article_id, self.amount)


@discriminate('type', 'refund')
class RefundLine(ReceiptLine):
    def __repr__(self):
        return 'RefundLine(super={})'.format(super(RefundLine, self).__repr__())


if __name__ == '__main__':
    import sys
    import traceback

    from serializer_utils.deserializer import deserialize

    try:
        print(deserialize(ReceiptLine, {'type': 'transaction', 'name': 'asdf', 'article_id': 5, 'amount': 5}))
        print(deserialize(ReceiptLine, {'type': 'refund', 'name': 'asdf', 'pk': 5}))
        print(deserialize(ReceiptLine, {'type': 'other', 'name': 'asdf'}))
    except TypeError as err:
        sleep(0.05)
        print(traceback.format_exc(), file=sys.stderr)
