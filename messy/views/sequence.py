
from messy.views import (BaseViewer, r, get_dbhandler, m_roles, ParseFormError, form_submit_bar,
                         render_to_response, form_submit_bar, select2_lookup, error_page,
                         Response, modal_delete, modal_error, Response, HTTPFound,
                         generate_file_table)
import rhombus.lib.tags_b46 as t
import dateutil


class SequenceViewer(BaseViewer):
    """
        Design outline
        --------------

        SequenceViewer performs sequence data visualization and limited editing,
        as most of the data in Sequence object should be uploaded with output of
        analysis software and/or data processing pipelines.

    """


    managing_roles = BaseViewer.managing_roles + [r.SEQUENCE_MANAGE]
    modifying_roles = managing_roles + [r.SEQUENCE_MODIFY]

    object_class = get_dbhandler().Sequence
    fetch_func = get_dbhandler().get_sequences_by_ids
    edit_route = 'messy.sequence-edit'
    view_route = 'messy.sequence-view'

    form_fields = {
        'sequencingrun_id': ('messy-sequence-sequencingrun_id', ),
        'sample_id': ('messy-sequence-sample_id', ),
        'method_id': ('messy-sequence-method_id', ),
        'accid': ('messy-sequence-accid', ),
        'submission_date?': ('messy-sequence-submission_date', dateutil.parser.parse),
        'lineage_1': ('messy-sequence-lineage_1', ),
        'prob_1': ('messy-sequence-prob_1', float),
        'lineage_2': ('messy-sequence-lineage_2', ),
        'prob_2': ('messy-sequence-prob_2', float),
        'lineage_3': ('messy-sequence-lineage_2', ),
        'prob_3': ('messy-sequence-prob_2', float),
        'avg_depth': ('messy-sequence-avg_depth'),
        'length': ('messy-sequence-length', ),
        'gaps': ('messy-sequence-gaps', ),
        'depth_plot?': ('messy-sequence-depth_plot', lambda x: x.file.read() if x != b'' else None),
        'sequence': ('messy-sequence-sequence', ),
    }

    @m_roles(r.PUBLIC)
    def index(self):

        sequences = self.dbh.get_sequences(groups=None, fetch=False)
        html, code = generate_sequence_table(sequences, self.request)
        html = t.div()[t.h2('Sequences'), html]

        return render_to_response("messy:templates/generic_page.mako",
                                  {'html': html, },
                                  request=self.request)

    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):

        obj = obj or self.obj
        dbh = self.dbh
        ff = self.form_fields

        # dealing with all input_select values
        sequencingrun = obj.sequencingrun
        sample = obj.sample

        eform = t.form(name='messy-sample', method=t.POST, enctype=t.FORM_MULTIPART)[
            self.hidden_fields(obj),
            t.fieldset(
                t.input_select(ff['sequencingrun_id'][0], 'Sequencing Run', value=obj.sequencingrun_id,
                               offset=2, size=3, static=readonly,
                               options=[(sequencingrun.id, sequencingrun.code)] if sequencingrun else []),
                t.input_select(ff['sample_id'][0], 'Sample', value=obj.sample_id,
                               offset=2, size=4, static=readonly,
                               options=[(sample.id, f'{sample.code} | {sample.collection.code}')] if sample else []),
                t.input_text(ff['accid'][0], 'Acc ID', value=obj.accid,
                             offset=2, static=readonly, update_dict=update_dict),
                t.input_text(ff['submission_date?'][0], 'Submission Date', value=obj.submission_date,
                             offset=2, static=readonly, update_dict=update_dict),
            ),
            t.fieldset(
                form_submit_bar(create) if not readonly else t.div(),
                name='footer'
            ),
        ]

        return t.div()[t.h2('Sequence'), eform], ''


def generate_sequence_table(sequences, request):

    table_body = t.tbody()

    not_guest = not request.user.has_roles(r.GUEST)

    for sequence in sequences:
        sample = sequence.sample
        table_body.add(
            t.tr(
                t.td(t.literal('<input type="checkbox" name="sequence-ids" value="%d" />' % sequence.id)
                     if not_guest else ''),
                t.td(t.a(sample.code, href=request.route_url('messy.sequence-view', id=sequence.id))),
                t.td(sequence.accid),
                t.td(sample.sequence_name),
                t.td(sample.location),
                t.td(sample.collection_date),
                t.td(sample.lineage_1),
            )
        )

    sequence_table = t.table(class_='table table-condensed table-striped')[
        t.thead(
            t.tr(
                t.th('', style="width: 2em"),
                t.th('Code'),
                t.th('Acc ID'),
                t.th('Name'),
                t.th('Location'),
                t.th('Collection Date'),
                t.th('Lineage 1'),
            )
        )
    ]

    sequence_table.add(table_body)

    if not_guest:
        add_button = ('New sequence',
                      request.route_url('messy.sequence-add'))

        bar = t.selection_bar('sequence-ids', action=request.route_url('messy.sequence-action'),
                              add=add_button)
        html, code = bar.render(sequence_table)

    else:
        html = t.div(sequence_table)
        code = ''

    return html, code

# EOF
