

function buildReport() {
    var totalReport = null;
    var contigsLengths = null;
    var alignedContigsLengths = null;
    var referenceLength = 0;
    var contigs = null;
    var genes = null;
    var operons = null;
    var gcInfos = null;

    var glossary = JSON.parse($('#glossary-json').html());

    var plotsSwitchesDiv = document.getElementById('plots-switches');
    var plotPlaceholder = document.getElementById('plot-placeholder');
    var legendPlaceholder = document.getElementById('legend-placeholder');
    var scalePlaceholder = document.getElementById('scale-placeholder');

//    var colors = ["#FF5900", "#008FFF", "#168A16", "#7C00FF", "#00B7FF", "#FF0080", "#7AE01B", "#782400", "#E01B6A"];
    var colors = [
        '#0000FF', //blue
        '#008000', //green
        '#FFA500', //orange
        '#00FFFF', //aqua
        '#FF0000', //red
        '#FF00FF', //fushua
        '#CCCC00', //yellow
        '#800000', //maroon
        '#808080', //gray
        '#000080', //navy
        '#808000', //olive
        '#800080', //purple
        '#00FF00', //lime
        '#008080', //team
    ];

    function distinctColors(count) {
        var colors = [];
        for(var hue = 0; hue < 360; hue += 360 / count) {
            var color = hsvToRgb(hue, 100, 100);
            var colorStr = '#' + color[0].toString(16) + color[1].toString(16) + color[2].toString(16);
                colors.push();
        }
        return colors;
    }

    var filenames;

    function getToggleFunction(name, drawPlot, data, refLen) {
        return function() {
            this.parentNode.getElementsByClassName('selected-switch')[0].className = 'plot-switch dotted-link';
            this.className = 'plot-switch selected-switch';
            togglePlots(name, drawPlot, data, refLen)
        };
    }

    var toRemoveRefLabel = true;
    function togglePlots(name, drawPlot, data, refLen) {
        if (name == 'cumulative') {
            $(plotPlaceholder).addClass('cumulative-plot-placeholder');
            if (referenceLength) {
                $('#legend-placeholder').append(
                    '<div id="reference-label">' +
                        '<label for="label_' + filenames.length + '_id" style="color: #000000;">' +
                            '<input type="checkbox" name="' + filenames.length +
                            '" checked="checked" id="label_' + filenames.length +
                            '_id">&nbsp;' + 'Reference,&nbsp;' +
                            toPrettyStringWithDimension(referenceLength, 'bp') +
                        '</label>' +
                    '</div>');
            }
            toRemoveRefLabel = true;
        } else {
            $(plotPlaceholder).removeClass('cumulative-plot-placeholder');
            if (toRemoveRefLabel) {
                var el = $('#reference-label');
                el.remove();
                toRemoveRefLabel = false;
            }
        }

        $(scalePlaceholder).html('');
        drawPlot(name, colors, filenames, data, refLen, plotPlaceholder, legendPlaceholder, glossary, scalePlaceholder);
    }

    var firstPlot = true;
    function makePlot(name, title, drawPlot, data, refLen) {
        var switchSpan = document.createElement('span');
        switchSpan.id = name + '-switch';
        switchSpan.innerHTML = title;
        plotsSwitchesDiv.appendChild(switchSpan);

        if (firstPlot) {
            switchSpan.className = 'plot-switch selected-switch';
            togglePlots(name, drawPlot, data, refLen);
            firstPlot = false;

        } else {
            switchSpan.className = 'plot-switch dotted-link';
        }

        $(switchSpan).click(getToggleFunction(name, drawPlot, data, refLen));
    }

    try { referenceLength = JSON.parse($('#reference-length-json').html()).reflen; } catch (e) { referenceLength = null; }
    try { totalReport = JSON.parse($('#total-report-json').html()); } catch (e) { totalReport = null; }
    if (totalReport) {
        filenames = totalReport.assembliesNames;

        if (filenames.length == 0) {
            return 1;
        }

        var qualities = null;
        var mainMetrics = null;
        try { qualities = JSON.parse($('#qualities-json').html()); } catch (e) { alert(e.stack); qualities = null; }
        try { mainMetrics = JSON.parse($('#main-metrics-json').html()); } catch (e) { alert(e.message); mainMetrics = null; }

//        colors = distinctColors(filenames.length);

//        document.title += (totalReport.date);
        $('#subheader').html(totalReport.date + '.');
        $('#mincontig').append('Contigs of length ≥ ' + totalReport.minContig + ' bp are used.');
        $('#extended_link').append('<a class="dotted-link" id="extended_report_link">Extended report</a>');

        buildTotalReport(filenames, totalReport.report, glossary, qualities, mainMetrics);

        $('#extended_report_link').click(function() {
            $('.content-row-hidden').fadeToggle('fast');

            var link = $('#extended_report_link');
            if (link.html() == 'Extended report') {
                link.html('Compact report');
            } else {
                link.html('Extended report')

            }
        })
    } else {
        return 1;
    }

    filenames.forEach(function(filename, i) {
        var id = 'label_' + i + '_id';
        $('#legend-placeholder').append('<div>' +
            '<label for="' + id + '" style="color: ' + colors[i] + '">' +
            '<input type="checkbox" name="' + i + '" checked="checked" id="' + id + '">&nbsp;' + filename + '</label>' +
            '</div>');
    });

    try { contigsLengths = JSON.parse($('#contigs-lengths-json').html()); } catch (e) { contigsLengths = null; }
    if (contigsLengths) {
        makePlot('cumulative', 'Cumulative length',
            drawCumulativePlot,
            contigsLengths.lists_of_lengths,
            referenceLength
        );
        makePlot('nx', 'Nx',
            drawNxPlot,
            contigsLengths.lists_of_lengths,
            null
        );
//        drawCumulativePlot(contigsLengths.filenames, contigsLengths.lists_of_lengths, referenceLength, $('#cumulative-plot-div'), null,  glossary);
//        drawNxPlot(contigsLengths.filenames, contigsLengths.lists_of_lengths, 'Nx', null, $('#nx-plot-div'), null,  glossary);
    }

    try { alignedContigsLengths = JSON.parse($('#aligned-contigs-lengths-json').html()); } catch (e) { alignedContigsLengths = null; }

    if (alignedContigsLengths) {
        makePlot('nax', 'NAx', drawNxPlot,
            alignedContigsLengths.lists_of_lengths,
            null
        );
//        drawNxPlot(alignedContigsLengths.filenames, alignedContigsLengths.lists_of_lengths, 'NAx', null, $('#nax-plot-div'), null,  glossary);
    }

    if (contigsLengths && referenceLength) {
        makePlot('ngx', 'NGx', drawNxPlot,
            contigsLengths.lists_of_lengths,
            referenceLength
        );
//        drawNxPlot(contigsLengths.filenames, contigsLengths.lists_of_lengths, 'NGx',referenceLength, $('#ngx-plot-div'), null,  glossary);
    }
    if (alignedContigsLengths && referenceLength) {
        makePlot('ngax', 'NGAx', drawNxPlot,
            alignedContigsLengths.lists_of_lengths,
            referenceLength
        );
//        drawNxPlot(alignedContigsLengths.filenames, alignedContigsLengths.lists_of_lengths, 'NGAx', referenceLength, $('#ngax-plot-div'), null,  glossary);
    }

    contigsLengths = null;
    alignedContigsLengths = null;

    try { genes = JSON.parse($('#genes-json').html()); } catch (e) { genes = null; }
    try { operons = JSON.parse($('#operons-json').html()); } catch (e) { operons = null; }
    if (genes || operons) {
        try { contigs = JSON.parse($('#contigs-json').html()); } catch (e) { contigs = null; }
    }

    if (contigs) {
        if (genes) {
            makePlot('genes', 'Genes', drawGenesPlot,  {
                    contigsInfos: contigs.contigs,
                    genes: genes.genes,
                    found: genes.found,
                    kind: 'gene',
                },
                referenceLength
            );
//            drawGenesPlot(contigs.filenames, contigs.contigs, genes.genes, genes.found, 'gene', $('#genes-plot-div'), null,  glossary);
        }
        if (operons) {
            makePlot('operons', 'Operons', drawGenesPlot, {
                    contigsInfos: contigs.contigs,
                    genes: operons.operons,
                    found: operons.found,
                    kind: 'operon',
                },
                referenceLength
            );
//            drawGenesPlot(contigs.filenames, contigs.contigs, operons.operons, operons.found, 'operon', $('#operons-plot-div'), null,  glossary);
        }
    }

    contigs = null;
    genes = null;
    operons = null;

    try { gcInfos = JSON.parse($('#gc-json').html()); } catch (e) { gcInfos = null; }

    if (gcInfos) {
        makePlot('gc', 'GC content', drawGCPlot, gcInfos.lists_of_gc_info, referenceLength);
//        drawGCPlot(gcInfos.filenames, gcInfos.lists_of_gc_info, $('#gc-plot-div'), null, glossary);
    }

    gcInfos = null;

    return 1;
}

