"""
nf_tables expression netlink attributes

See EXPRESSIONS in nft(8).
"""

from pyroute2.nftables.parser.parser import nfta_nla_parser, conv_map_tuple


class NFTReg(object):

    def __init__(self, num):
        self.num = num

    @classmethod
    def from_netlink(cls, nlval):
        # please, for more information read nf_tables.h.
        if nlval == 'NFT_REG_VERDICT':
            num = 0
        else:
            num = int(nlval.split('_')[-1].lower())
            if nlval.startswith('NFT_REG32_'):
                num += 8
        return cls(num=num)

    @staticmethod
    def to_netlink(reg):
        # please, for more information read nf_tables.h.
        if reg.num == 0:
            return 'NFT_REG_VERDICT'
        if reg.num < 8:
            return 'NFT_REG_{0}'.format(reg.num)
        return 'NFT_REG32_{0}'.format(reg.num)

    @classmethod
    def from_dict(cls, val):
        return cls(num=val)

    def to_dict(self):
        return self.num


class NFTRuleExpr(nfta_nla_parser):

    #######################################################################
    conv_maps = (
        conv_map_tuple('name', 'NFTA_EXPR_NAME', 'type', 'raw'),
    )
    #######################################################################

    @classmethod
    def from_netlink(cls, expr_type, ndmsg):
        inst = super(NFTRuleExpr, cls).from_netlink(ndmsg)
        inst.name = expr_type
        return inst

    cparser_reg = NFTReg


    class cparser_extract_str(object):
        STRVAL = None

        @classmethod
        def from_netlink(cls, val):
            magic = '{0}'
            left, right = cls.STRVAL.split(magic, 1)
            if right:
                val = val[len(left):-len(right)]
            else:
                val = val[len(left):]
            return val.lower()

        @classmethod
        def to_netlink(cls, val):
            return cls.STRVAL.format(val).upper()

        @staticmethod
        def from_dict(val):
            return val

        @staticmethod
        def to_dict(val):
            return val


class ExprMeta(NFTRuleExpr):

    conv_maps = NFTRuleExpr.conv_maps + (
        conv_map_tuple('key', 'NFTA_META_KEY', 'key', 'meta_key'),
        conv_map_tuple('dreg', 'NFTA_META_DREG', 'dreg', 'reg'),
    )

    class cparser_meta_key(NFTRuleExpr.cparser_extract_str):
        STRVAL = 'NFT_META_{0}'


NFTA_EXPR_NAME_MAP = {
    'meta': ExprMeta,
}


def get_expression_from_netlink(ndmsg):
    name = ndmsg.get_attr('NFTA_EXPR_NAME')
    try:
        expr_cls = NFTA_EXPR_NAME_MAP[name]
    except KeyError:
        raise NotImplementedError(
            "can't load rule expression {0} from netlink {1}".format(name, ndmsg))
    return expr_cls.from_netlink(name, ndmsg.get_attr('NFTA_EXPR_DATA'))


def get_expression_from_dict(d):
    name = d['type']
    if name in NFTA_EXPR_NAME_MAP:
        expr_cls = NFTA_EXPR_NAME_MAP[name]
    else:
        raise NotImplementedError(
            "can't load rule expression {0} from json {1}".format(name, d))
    return expr_cls.from_dict(d)
