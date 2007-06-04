#!/usr/bin/python2.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
#
#    Copyright (C) 1999-2006  Keith Dart <keith@kdart.com>
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.

"""

"""

import qatest

import SMI.SMI as SMI

MIBS = ["TUBS-IBR-TEST-MIB", "SNMPv2-SMI", "COFFEE-POT-MIB", "TCP-MIB", "IF-MIB"]

class SMIBaseTest(qatest.Test):
    pass

class SMIInitTest(SMIBaseTest):
    """Check that the SMI basically works. The fact that we got this far (no
import errors above) is most of what this test needs.  """
    def test_method(self):
        # It turns out that if smiExit is registered with atexit then the
        # interpreter will segfault at exit.
        #
        # These modules are pre-loaded by the SMI module.
        for modname in ("SNMPv2-SMI", "SNMPv2-TC", "SNMPv2-CONF"):
            self.assert_true(SMI.is_loaded(modname))
        return self.passed("All initial modules loaded.")

class FlagsTest(SMIBaseTest):
    def test_method(self):
        flags = SMI.Flags.get_flags()
        self.assert_true(flags == 0)
        for flag in ( SMI.SMI_FLAG_ERRORS, SMI.SMI_FLAG_NODESCR,
                    SMI.SMI_FLAG_RECURSIVE, SMI.SMI_FLAG_STATS,
                    SMI.SMI_FLAG_VIEWALL):
            SMI.Flags.set(flag)
            self.assert_true(SMI.Flags.test(flag))
            self.info("Flag set: %s" % (SMI.Flags.toString(),))
            SMI.Flags.clear(flag)
            self.assert_false(SMI.Flags.test(flag))
            self.info("Flag cleared %s" % (SMI.Flags.toString(),))
        return self.passed("all assertions passed")


### Module class tests
class ModuleNew(SMIBaseTest):
    def test_method(self):
        map(SMI.load_module, MIBS)
        m = SMI.get_module(MIBS[0])
        self.assert_true(m.name == MIBS[0])
        self.config.testModule = m
        return self.passed()

class ModuleImports(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("ModuleNew")]
    def test_method(self):
        m = self.config.testModule
        self.info("Imports for %s:" % (m.name,))
        imps = m.get_imports()
        for imp in imps:
            self.info(imp)
        return self.passed("got imports")

class ModuleType(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("ModuleNew")]
    def test_method(self):
        m = SMI.get_module("TUBS-IBR-TEST-MIB")
        t = m.get_type("OctalValue")
        self.info(t)
        if t is None:
            return self.abort("The tested module returned no Type")
        self.assert_equal(t.name, "OctalValue")
        return self.passed("got specified type")

class ModuleTypes(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("ModuleNew")]
    def test_method(self):
        m = self.config.testModule
        got = 0
        self.info("Got type list:")
        for tp in m.get_types():
            self.verboseinfo(tp)
            got = 1
        if got:
            return self.passed("got type list")
        else:
            return self.failed("failed to get type list!")

class ModuleRevisions(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("ModuleNew")]
    def test_method(self):
        m = self.config.testModule
        revs = m.get_revisions()
        self.info("Got revisions list:")
        for rev in revs:
            self.info(rev)
        #self.assert_true(revs)
        return self.passed("Got revisions")

class ModuleImported(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("ModuleNew")]
    def test_method(self):
        m = SMI.get_module(MIBS[0])
        m2 = SMI.get_module("SNMPv2-SMI")
        self.assert_true(m.is_imported(m2, "Integer32"))
        self.assert_false(m.is_imported(m2, "Counter64"))
        return self.passed("All is_imported assertions passed.")

class ModuleMacro(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("ModuleNew")]
    def test_method(self):
        m = SMI.get_module("SNMPv2-SMI")
        mac = m.get_macro("NOTIFICATION-TYPE")
        self.verboseinfo(mac)
        self.assert_equal(mac.name, "NOTIFICATION-TYPE")
        return self.passed("Got macro.")

class ModuleMacros(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("ModuleNew")]
    def test_method(self):
        got = 0
        m = SMI.get_module("SNMPv2-SMI")
        for mac in m.get_macros():
            self.info(mac)
            got = 1
        if got:
            return self.passed("got macros")
        else:
            return self.failed("no macros returned")

class ModuleNode(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("ModuleNew")]
    def test_method(self):
        m = self.config.testModule
        n = m.get_node("testMIB")
        self.assert_equal("testMIB", n.name)
        self.verboseinfo(n)
        return self.passed("got testMIB node")

class ModuleNodes(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("ModuleNew")]
    def test_method(self):
        m = self.config.testModule
        got = 0
        kind = SMI.SMI_NODEKIND_ANY
        nodes = m.get_nodes(kind)
        self.info("nodes of kind %d" % (kind,))
        for node in nodes:
            self.info(node.name)
            got = 1
        if got:
            return self.passed("got nodes")
        else:
            return self.failed("no nodes!")

class ModuleScalars(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("ModuleNew")]
    def test_method(self):
        m = SMI.get_module("TCP-MIB")
        got = 0
        for scalar in m.get_scalars():
            self.verboseinfo(scalar.name)
            got = 1
        if got:
            return self.passed("got scalars")
        else:
            return self.failed("no scalars!")

class ModuleTables(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("ModuleNew")]
    def test_method(self):
        m = SMI.get_module("TCP-MIB")
        got = 0
        for table in m.get_tables():
            self.verboseinfo(table.name)
            got = 1
        if got:
            return self.passed("got tables")
        else:
            return self.failed("no tables!")

class ModuleRows(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("ModuleNew")]
    def test_method(self):
        m = SMI.get_module("TCP-MIB")
        got = 0
        for row in m.get_rows():
            self.verboseinfo(row.name)
            got = 1
        if got:
            return self.passed("got rows")
        else:
            return self.failed("no rows!")

class ModuleColumns(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("ModuleNew")]
    def test_method(self):
        m = SMI.get_module("TCP-MIB")
        got = 0
        for col in m.get_columns():
            self.verboseinfo(col.name)
            got = 1
        if got:
            return self.passed("got columns")
        else:
            return self.failed("no columns!")

class ModuleNotifications(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("ModuleNew")]
    def test_method(self):
        m = SMI.get_module("IF-MIB")
        got = 0
        for notif in m.get_notifications():
            self.verboseinfo(notif)
            got = 1
        if got:
            return self.passed("got notifications")
        else:
            return self.failed("no notifications!")

class ModuleCompliances(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("ModuleNew")]
    def test_method(self):
        m = SMI.get_module("IF-MIB")
        got = 0
        for comp in m.get_compliances():
            self.verboseinfo(comp)
            got = 1
        if got:
            return self.passed("got compliances")
        else:
            return self.failed("no compliances!")

class ModuleGroups(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("ModuleNew")]
    def test_method(self):
        m = SMI.get_module("IF-MIB")
        got = 0
        for grp in m.get_groups():
            self.verboseinfo(grp)
            got = 1
        if got:
            return self.passed("got groups")
        else:
            return self.failed("no groups!")

class ModuleCapabilities(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("ModuleNew")]
    def test_method(self):
        m = SMI.get_module("XXX ") # XXX what module has capabilities?
        got = 0
        for cap in m.get_capabilities():
            self.verboseinfo(cap)
            got = 1
        if got:
            return self.passed("got capabilities")
        else:
            return self.failed("no capabilities!")


class ModuleIdentityNode(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("ModuleNew")]
    def test_method(self):
        m = self.config.testModule
        idn = m.identityNode
        self.verboseinfo(idn)
        if idn:
            return self.passed("got identity node")
        else:
            return self.failed("did not get identity node")

class ModuleDestroy(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("ModuleNew")]
    def test_method(self):
        del self.config.testModule
        return self.passed("deleted module")


class NodeNew(SMIBaseTest):
    def test_method(self):
        got = 0
        mod = SMI.get_module("TCP-MIB")
        nodes = list(mod.get_nodes(SMI.SMI_NODEKIND_ANY))
        self.assert_true(len(nodes) > 1)
        return self.passed("got nodes")

class NodeChildren(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("NodeNew")]
    def test_method(self):
        got = 0
        mod = SMI.get_module("TCP-MIB")
        scalars = list(mod.get_scalars())
        table = mod.get_tables().next()
        for child in table.get_children():
            self.verboseinfo(child)
            got += 1
        if got:
            self.config.testtable = table
            self.config.testchild = child
            return self.passed("got %d children" % (got,))
        else:
            return self.failed("no children!")

class NodeParent(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("NodeChildren")]
    def test_method(self):
        # table and child stashed by NodeChildren test
        table = self.config.testtable
        del self.config.testtable
        child = self.config.testchild
        parent = child.get_parent()
        self.assert_equal(parent.name, table.name)
        self.assert_equal(parent.OID, table.OID)
        return self.passed("got correct parent")


class NodeRelated(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("NodeChildren")]
    def test_method(self):
        mod = SMI.get_module("IF-MIB")
        node = mod.get_node("ifXEntry")
        rel = node.get_related() # gets AUGMENTS node
        if rel and rel.name == "ifEntry":
            return self.passed("got correct relation")
        else:
            return self.failed("failed to get proper augmentation!")

class NodeModule(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("NodeChildren")]
    def test_method(self):
        child = self.config.testchild
        mod = child.get_module()
        self.assert_equal(mod.name, "TCP-MIB")
        return self.passed("got correct module")

class NodeLine(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("NodeChildren")]
    def test_method(self):
        c = self.config.testchild  # last test deletes the node!
        l = c.get_line()
        self.info("%s defined on line %d in module %s" % (c.name, l, c.get_module().name))
        self.assert_true(l > 0)
        return self.passed("got node line number")

class NodeType(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("NodeChildren")]
    def test_method(self):
        child = self.config.testchild.get_children().next()
        del self.config.testchild  # last test deletes the node!
        t = child.get_type()
        self.verboseinfo(t)
        self.info("NamedNumbers:")
        got = 0
        for nn in t.get_named_numbers():
            self.info(nn)
            got += 1
        if got:
            return self.passed("got %d named numbers" % (got,))
        else:
            return self.failed("did not get any named numbers")


class getNodeByOID(SMIBaseTest):
    PREREQUISITES = [qatest.PreReq("ModuleNew")]
    def test_method(self):
        n = SMI.get_node_by_OID("1.3.6.1.4.1.1575.1.7")
        self.assert_equal(n.name, "testMIB")
        return self.passed("got node by OID")


###### suite #################################
class SMISuite(qatest.TestSuite):
    # delete or override this as necessary. 
    def initialize(self):
        pass

    # delete or override this as necessary. 
    def finalize(self):
        pass


# suite factory function. register tests here.
def get_suite(conf):
    suite = SMISuite(conf)
    # global tests
    suite.add_test(SMIInitTest)
    suite.add_test(FlagsTest)

    # Module class tests
    suite.add_test(ModuleNew)
    suite.add_test(ModuleIdentityNode)
    suite.add_test(ModuleImports)
    suite.add_test(ModuleType)
    suite.add_test(ModuleTypes)
    suite.add_test(ModuleRevisions)
    suite.add_test(ModuleImported)
    suite.add_test(ModuleMacro)
    suite.add_test(ModuleMacros)
    suite.add_test(ModuleNode)
    suite.add_test(ModuleNodes)
    suite.add_test(ModuleScalars)
    suite.add_test(ModuleTables)
    suite.add_test(ModuleRows)
    suite.add_test(ModuleColumns)
    suite.add_test(ModuleNotifications)
    suite.add_test(ModuleCompliances)
    suite.add_test(ModuleGroups)
#   suite.add_test(ModuleCapabilities)
    suite.add_test(getNodeByOID)
    suite.add_test(ModuleDestroy)

    # node class tests
    suite.add_test(NodeNew)
    suite.add_test(NodeChildren)
    suite.add_test(NodeParent)
    suite.add_test(NodeRelated)
    suite.add_test(NodeModule)
    suite.add_test(NodeLine)
    suite.add_test(NodeType)
    
    return suite


def run(conf):
    suite = get_suite(conf)
    suite()

if __name__ == "__main__":
    import config
    cf = config.get_config()
    run(cf)

