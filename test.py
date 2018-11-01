from time import sleep
from typing import Optional, List

from serializer_utils.deserializer import Deserializable, Rule
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


class Test(Deserializable):
    tf: Optional[ReceiptLine]
    ns: List[int]

    def __repr__(self):
        return 'Test(tf={},ns={})'\
            .format(self.tf.__repr__(), self.ns.__repr__())


if __name__ == '__main__':
    import sys
    import traceback

    from serializer_utils.deserializer import deserialize

    def print_result(function, *args, **kwargs):
        try:
            print(function(*args, **kwargs))
        except:
            sleep(0.05)
            print(traceback.format_exc(), file=sys.stderr)

    fns = [
        [Rule(ReceiptLine), {'type': 'transaction', 'name': 'asdf', 'article_id': 5, 'amount': 5}],
        [Rule(ReceiptLine), {'type': 'refund', 'name': 'asdf', 'pk': 5}],
        [Rule(ReceiptLine), {'type': 'other', 'name': 'asdf'}],
        [Rule(ReceiptLine), {'type': 'transaction'}],
        [Rule(ReceiptLine), {'type': 'transaction', 'name': 'asdf', 'pk': 'no'}],
        [Rule(Test), {'tf': {'type': 'refund', 'name': 'asdf', 'pk': 5},
                      'ns': [1, 2, 4, 7, 9]}]
    ]

    [print_result(deserialize, *entry) for entry in fns]
