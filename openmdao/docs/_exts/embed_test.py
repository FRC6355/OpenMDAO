import sys

from docutils import nodes
from docutils.parsers.rst.directives import unchanged


import sphinx
from sphinx.util.compat import Directive
from sphinx.writers.html import HTMLTranslator

from openmdao.docs._utils.docutil import get_unit_test_source_and_run_outputs, get_unit_test_source_and_run_outputs_in_out

if sys.version_info[0] == 2:
    import cgi as cgiesc
else:
    import html as cgiesc


class skipped_or_failed_node(nodes.Element):
    pass


def visit_skipped_or_failed_node(self, node):
    pass


def depart_skipped_or_failed_node(self, node):
    if not isinstance(self, HTMLTranslator):
        self.body.append("output only available for HTML\n")
        return

    html = '<div class="output"><div class="prompt output_prompt">Out&nbsp;[{}]:<div class="{}"><pre>{}</pre></div>'.format(node["number"], node["kind"], cgiesc.escape(node["text"]))
    self.body.append(html)

class in_or_out_node(nodes.Element):
    pass

def visit_in_or_out_node(self, node):
    pass

def depart_in_or_out_node(self, node):
    if not isinstance(self, HTMLTranslator):
        self.body.append("output only available for HTML\n")
        return
    if node["kind"] == "In":
        html = '<div class="container"><div class="cell border-box-sizing code_cell rendered"><div class="input"><div class="prompt input_prompt">{}&nbsp;[{}]:</div><div class="inner_cell"><div class="input_area"><div class=" highlight hl-ipython3"><pre>{}</pre></div></div></div></div></div></div>'.format(node["kind"], node["number"], node["text"])
    elif node["kind"] == "Out":
        html = '<div class="container"><div class="cell border-box-sizing code_cell rendered"><div class="output"><div class="prompt output_prompt">{}&nbsp;[{}]:</div><div class="inner_cell"><div class="output_area"><div class=" highlight hl-ipython3"><pre>{}</pre><br></div></div></div></div></div></div>'.format(node["kind"], node["number"], node["text"])

    self.body.append(html)


class EmbedTestDirective(Directive):
    """EmbedTestDirective is a custom directive to allow a unit test and the result
    of running the test to be shown in feature docs.
    An example usage would look like this:

    .. embed-test::
        openmdao.core.tests.test_indep_var_comp.TestIndepVarComp.test___init___1var

    What the above will do is replace the directive and its args with the blocks of code
    from the unit test, run the test with the asserts replaced with prints, and show the
    resulting outputs. The code will be split into a new block following every print
    statement. Each block of code will be followed by a block showing the result of the
    print statement.

    There is also an option to the directive that lets the developer show all the code in one
    block followed by all the outputs in one block. There is no splitting up of the code
    on print statements. This is the old way of doing it.

    .. embed-test::
        openmdao.core.tests.test_component.TestIndepVarComp.test___init___1var
        :no-split:

    """

    # must have at least one directive for this to work
    required_arguments = 1
    optional_arguments = 1
    has_content = True

    option_spec = {
        'no-split': unchanged
    }

    def run(self):
        # create a list of document nodes to return
        doc_nodes = []
        n = 1
        # grabbing source, and output of a test segment
        method_path = self.arguments[0]
        if 'no-split' in self.options:
            src, output, skipped, failed = get_unit_test_source_and_run_outputs(method_path)
            # we want the body of test code to be formatted and code highlighted
            body = in_or_out_node(kind="In", number=n, text=src)
            body['language'] = 'python'
            doc_nodes.append(body)

            # we want the output block to also be formatted similarly unless test was skipped
            if skipped:
                output = "Test skipped because " + output
                output_node = skipped_or_failed_node(text=output, number=n, kind="skipped")
            elif failed:
                output_node = skipped_or_failed_node(text=output, number=n, kind="failed")
            else:
                output_node = in_or_out_node(kind="Out", number=n, text=src)

            doc_nodes.append(output_node)

        else:
            src, skipped_failed_output, input_blocks, output_blocks, skipped, failed = get_unit_test_source_and_run_outputs_in_out(method_path)

            if skipped or failed: # do the old way
                # we want the body of test code to be formatted and code highlighted
                #body = nodes.literal_block(src, src)
                body = in_or_out_node(kind="In", number=n, text=src, language="python")
                #body['language'] = 'python'
                doc_nodes.append(body)

                # we want the output block to also be formatted similarly unless test was skipped
                if skipped:
                    output = "Test skipped because " + skipped_failed_output
                    output_node = skipped_or_failed_node(text=output, number=n, kind="skipped")
                elif failed:
                    output_node = skipped_or_failed_node(text=skipped_failed_output, number=n, kind="failed")

                doc_nodes.append(output_node)

            else:
                for input_block, output_block in zip(input_blocks, output_blocks):
                    #input_node = nodes.literal_block(input_block, input_block)
                    input_node = in_or_out_node(kind="In", number=n, text=input_block)

                    input_node['language'] = 'python'
                    doc_nodes.append(input_node)

                    #output_node = nodes.literal_block(output_block, output_block)
                    output_node = in_or_out_node(kind="Out", number=n, text=output_block)
                    doc_nodes.append(output_node)

                    n = n + 1

        return doc_nodes


def setup(app):
    """add custom directive into Sphinx so that it is found during document parsing"""
    app.add_directive('embed-test', EmbedTestDirective)
    app.add_node(skipped_or_failed_node, html=(visit_skipped_or_failed_node, depart_skipped_or_failed_node))
    app.add_node(in_or_out_node, html=(visit_in_or_out_node, depart_in_or_out_node))

    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
