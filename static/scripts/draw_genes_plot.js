
var gns = {
    maxY: 0,
    maxYTick: 0,
    series: null,
    draw: null,
    redraw: null,
    kind: null,
    yAxisLabeled: false,
};

function drawGenesPlot(name, colors, filenames, data, referenceLength,
                       div, legendPlaceholder, glossary) {
//    div.html(
//        "<span class='plot-header'>" + kind[0].toUpperCase() + kind.slice(1) + "s covered</span>" +
//        "<div class='plot-placeholder' id='" + kind + "s-plot-placeholder'></div>"
//    );

    if (gns.kind != name) {
        gns = {
            maxY: 0,
            maxYTick: 0,
            series: null,
            draw: null,
            redraw: null,
            kind: name,
        };
    }

    gns.yAxisLabeled = false;

    if (gns.series == null || gns.draw == null || gns.redraw == null) {
        var contigsInfos = data.contigsInfos;
        var genes = data.genes;
        var found = data.found;
        var kind = data.kind;

        var plotsN = filenames.length;
        gns.series = new Array(plotsN);

        gns.maxY = 0;
        gns.maxX = 0;

        for (var fi = 0; fi < plotsN; fi++) {
            var filename = filenames[fi];
            var contigs = contigsInfos[filename];
            for (var i = 0; i < genes.length; i++) {
                found[i] = 0
            }

            gns.series[fi] = {
                data: [[0, 0]],
                label: filenames[fi],
                number: fi,
                color: colors[fi],
            };

            var contigNo = 0;
            var totalFull = 0;

            for (var k = 0; k < contigs.length; k++) {
                var alignedBlocks = contigs[k];
                contigNo += 1;

                for (i = 0; i < genes.length; i++) {
                    var g = genes[i];

                    if (found[i] == 0) {
                        for (var bi = 0; bi < alignedBlocks.length; bi++) {
                            var block = alignedBlocks[bi];

                            if (block[0] <= g[0] && g[1] <= block[1]) {
                                found[i] = 1;
                                totalFull += 1;
                                break;
                            }
                        }
                    }
                }

                gns.series[fi].data.push([contigNo, totalFull]);

                if (gns.series[fi].data[k][1] > gns.maxY) {
                    gns.maxY = gns.series[fi].data[k][1];
                }
            }

            if (contigs.length > gns.maxX) {
                gns.maxX = contigs.length;
            }
        }

        for (i = 0; i < plotsN; i++) {
            gns.series[i].lines = {
                show: true,
                lineWidth: 1,
            }
        }

    //    for (i = 0; i < plotsN; i++) {
    //        plotsData[i].points = {
    //            show: true,
    //            radius: 1,
    //            fill: 1,
    //            fillColor: false,
    //        }
    //    }


        gns.draw = function(plotsData, colors) {
            $.plot(div, plotsData, {
                shadowSize: 0,
                colors: colors,
                legend: {
                    container: $('useless-invisible-element-that-does-not-even-exist'),
                },
                grid: {
                    borderWidth: 1,
                },
                yaxis: {
                    min: 0,
                    labelWidth: 120,
                    reserveSpace: true,
                    lineWidth: 0.5,
                    color: '#000',
                    tickFormatter: function (val, axis) {
                        if (!gns.yAxisLabeled && val > gns.maxY) {
                            gns.yAxisLabeled = true;
                            var res = val + ' ' + kind;
                            if (val > 1) {
                                res += 's'
                            }
                            return res;
                        } else {
                            return val;
                        }
                    },
                    minTickSize: 1,
                },
                xaxis: {
                    min: 0,
                    max: gns.maxX,
                    lineWidth: 0.5,
                    color: '#000',
                    tickFormatter: getContigNumberTickFormatter(gns.maxX),
                    minTickSize: 1,
                },
            });
        };

        gns.redraw = function() {
            var newPlotsData = [];
            var newColors = [];

            $('#legend-placeholder').find('input:checked').each(function() {
                var number = $(this).attr('name');
                if (number && gns.series && gns.series.length > 0) {
                    i = 0;
                    do {
                        var series = gns.series[i];
                        i++;
                    } while (series.number != number && i <= gns.series.length);
//                    if (i != gns.plotsData.length) {
                    newPlotsData.push(series);
                    newColors.push(series.color);
//                    }
                }
            });

            if (newPlotsData.length == 0) {
                newPlotsData.push({
                    data: [],
                });
                newColors.push('#FFF');
            }

            gns.draw(newPlotsData, newColors);
        }
    }

    $.each(gns.series, function(i, series) {
        $('#legend-placeholder').find('#label_' + i + '_id').click(gns.redraw);
    });

    gns.redraw();

    $('#contigs_are_ordered').show();
}

