#!/usr/bin/env python3
from __future__ import absolute_import, print_function

import datetime
import re
from optparse import OptionParser
from sys import argv, exit, stderr, stdout

from six.moves import range

import HiggsAnalysis.CombinedLimit.calculate_pulls as CP
import ROOT

# tool to compare fitted nuisance parameters to prefit values.
#
# Also used to check for potential problems in RooFit workspaces to be used with combine
# (see https://twiki.cern.ch/twiki/bin/viewauth/CMS/HiggsWG/HiggsPAGPreapprovalChecks)

# import ROOT with a fix to get batch mode (http://root.cern.ch/phpBB3/viewtopic.php?t=3198)
hasHelp = False
for X in ("-h", "-?", "--help"):
    if X in argv:
        hasHelp = True
        argv.remove(X)
argv.append("-b-")

ROOT.gROOT.SetBatch(True)
# ROOT.gSystem.Load("libHiggsAnalysisCombinedLimit")
argv.remove("-b-")
if hasHelp:
    argv.append("-h")

parser = OptionParser(usage="usage: %prog [options] in.root  \nrun with --help to get list of options")
parser.add_option(
    "--vtol",
    "--val-tolerance",
    dest="vtol",
    default=0.30,
    type="float",
    help="Report nuisances whose value changes by more than this amount of sigmas",
)
parser.add_option(
    "--stol",
    "--sig-tolerance",
    dest="stol",
    default=0.10,
    type="float",
    help="Report nuisances whose sigma changes by more than this amount",
)
parser.add_option(
    "--vtol2",
    "--val-tolerance2",
    dest="vtol2",
    default=2.0,
    type="float",
    help="Report severely nuisances whose value changes by more than this amount of sigmas",
)
parser.add_option(
    "--stol2",
    "--sig-tolerance2",
    dest="stol2",
    default=0.50,
    type="float",
    help="Report severely nuisances whose sigma changes by more than this amount",
)
parser.add_option(
    "-a",
    "--all",
    dest="show_all_parameters",
    default=False,
    action="store_true",
    help="Print all nuisances, even the ones which are unchanged w.r.t. pre-fit values.",
)
parser.add_option(
    "-A",
    "--abs",
    dest="absolute_values",
    default=False,
    action="store_true",
    help="Report also absolute values of nuisance values and errors, not only the ones normalized to the input sigma",
)
parser.add_option(
    "-p",
    "--poi",
    dest="poi",
    default="r",
    type="string",
    help="Name of signal strength parameter (default is 'r' as per text2workspace.py)",
)
parser.add_option(
    "-f",
    "--format",
    dest="format",
    default="text",
    type="string",
    help="Output format ('text', 'latex', 'twiki'",
)
parser.add_option(
    "-g",
    "--histogram",
    dest="plotfile",
    default=None,
    type="string",
    help="If true, plot the pulls of the nuisances to the given file.",
)
parser.add_option(
    "",
    "--pullDef",
    dest="pullDef",
    default="",
    type="string",
    help="Choose the definition of the pull, see python/calculate_pulls.py for options",
)
parser.add_option(
    "",
    "--skipFitS",
    dest="skipFitS",
    default=False,
    action="store_true",
    help="skip the S+B fit, instead the B-only fit will be repeated",
)
parser.add_option(
    "",
    "--skipFitB",
    dest="skipFitB",
    default=False,
    action="store_true",
    help="skip the B-only fit, instead the S+B fit will be repeated",
)
parser.add_option(
    "",
    "--sortBy",
    dest="sortBy",
    default="correlation",
    type="string",
    help="choose 'correlation' or 'impact' to sort rows by correlation with or impact on --poi (largest to smallest absolute)",
)
parser.add_option(
    "",
    "--regex",
    dest="regex",
    default=".*",
    type="string",
    help="Include only nuisance parameters that passes the following regex filter",
)
parser.add_option(
    "-w",
    "--workspace",
    dest="workspace",
    default="",
    type="string",
    help="Workspace to use for evaluating NLL differences. If no workspace is passed, NLL differences won't be calculated.",
)
parser.add_option(
    "",
    "--max-nuis",
    dest="max_nuis",
    default=65,
    type="int",
    help="Maximum nuisances for a single plot. If more than the specified number of nuisance parameters exist they will be split across multiple plots.",
)

(options, args) = parser.parse_args()
if len(args) == 0:
    parser.print_usage()
    exit(1)

if options.pullDef != "" and options.pullDef not in CP.allowed_methods():
    exit("Method %s not allowed, choose one of [%s]" % (options.pullDef, ",".join(CP.allowed_methods())))

if options.pullDef and options.absolute_values:
    print("Pulls are always defined as absolute, will modify --absolute_values to False for you")
    options.absolute_values = False

if options.pullDef:
    options.show_all_parameters = True

if options.sortBy not in ["correlation", "impact", "dnll"]:
    exit("choose one of [ %s ] for --sortBy" % (",".join()["correlation", "impact", "dnll"]))
elif options.sortBy == "dnll" and (not options.workspace):
    exit("can only sort by deltaNLL if a workspace is provided, otherwise no dnll can be calcualted")

if options.regex != ".*":
    print("Including only nuisance parameters following this regex query:")
    print((options.regex))

setUpString = "diffNuisances run on %s, at %s with the following options ... " % (
    args[0],
    datetime.datetime.utcnow(),
) + str(options)

file = ROOT.TFile(args[0])
if file == None:
    raise RuntimeError("Cannot open file %s" % args[0])
fit_s = file.Get("fit_s") if not options.skipFitS else file.Get("fit_b")
fit_b = file.Get("fit_b") if not options.skipFitB else file.Get("fit_s")
prefit = file.Get("nuisances_prefit")
if fit_s == None or fit_s.ClassName() != "RooFitResult":
    raise RuntimeError("File %s does not contain the output of the signal fit 'fit_s'" % args[0])
if fit_b == None or fit_b.ClassName() != "RooFitResult":
    raise RuntimeError("File %s does not contain the output of the background fit 'fit_b'" % args[0])
if prefit == None or prefit.ClassName() != "RooArgSet":
    raise RuntimeError("File %s does not contain the prefit nuisances 'nuisances_prefit'" % args[0])

workspace = None
if options.workspace:
    workspace_file = ROOT.TFile(options.workspace, "READ")
    workspace = workspace_file.Get("w")

isFlagged = {}

# maps from nuisance parameter name to the row to be printed in the table
table = {}

# get the fitted parameters
fpf_b = fit_b.floatParsFinal()
fpf_s = fit_s.floatParsFinal()

pulls = []
dnlls = []

nuis_p_i = 0
title = "pull" if options.pullDef else "#theta"

"""
def getGraph(hist,shift):

   gr = ROOT.TGraphAsymErrors()
   gr.SetName(hist.GetName())
   for i in range(hist.GetNbinsX()):
     x = hist.GetBinCenter(i+1)+shift
     y = hist.GetBinContent(i+1)
     e = hist.GetBinError(i+1)
     gr.SetPoint(i,x,y)
     gr.SetPointError(i,float(abs(shift))*0.8,e)
   return gr
"""

# Compile regex object, since we will be checking regex patterns several times.
regex_NP_obj = re.compile(options.regex)

np_count = 0
for i in range(fpf_s.getSize()):
    nuis_s = fpf_s.at(i)
    name = nuis_s.GetName()
    nuis_p = prefit.find(name)
    if nuis_p == None:
        if not options.absolute_values and not (options.pullDef == "unconstPullAsym"):
            continue
    if bool(regex_NP_obj.match(name)):
        np_count += 1


n_hists = np_count // options.max_nuis
if np_count % options.max_nuis == 0:
    n_hists -= 1

hist_fit_b = []
hist_fit_s = []
hist_prefit = []
gr_fit_b = []
gr_fit_s = []
hist_dnll = []
hist_cdnll = []
for idx in range(((np_count - 1) // options.max_nuis) + 1):
    # Also make histograms for pull distributions:
    nbins = min(np_count, options.max_nuis, np_count - (options.max_nuis * idx))
    hist_fit_b += [ROOT.TH1F("fit_b %s" % idx, "B-only fit Nuisances;;%s %s" % (title, idx), nbins, 0, nbins)]
    hist_fit_s += [ROOT.TH1F("fit_s %s" % idx, "S+B fit Nuisances   ;;%s %s" % (title, idx), nbins, 0, nbins)]
    hist_prefit += [
        ROOT.TH1F(
            "prefit_nuisancs %s" % idx,
            "Prefit Nuisances    ;;%s %s" % (title, idx),
            nbins,
            0,
            nbins,
        )
    ]
    # Store also the *asymmetric* uncertainties
    gr_fit_b += [ROOT.TGraphAsymmErrors()]
    gr_fit_b[idx].SetTitle("fit_b_g % s" % idx)
    gr_fit_s += [ROOT.TGraphAsymmErrors()]
    gr_fit_s[idx].SetTitle("fit_b_s % s" % idx)

    hist_dnll += [ROOT.TH1F("dnll %s" % idx, "delta log-likelihoods   ;;%s %s" % (title, idx), nbins, 0, nbins)]
    hist_cdnll += [ROOT.TH1F("cdnll %s" % idx, "cumulative delta log-likelihoods   ;;%s %s" % (title, idx), nbins, 0, nbins)]

error_poi = fpf_s.find(options.poi).getError()

# loop over all fitted parameters
for i in range(fpf_s.getSize()):
    nuis_s = fpf_s.at(i)
    name = nuis_s.GetName()
    nuis_b = fpf_b.find(name)
    nuis_p = prefit.find(name)

    # Skip this nuisance parameter if its name does not match the regex pattern.
    # The default pattern is .*
    # which will always match any name.
    if not bool(regex_NP_obj.match(name)):
        continue

    # keeps information to be printed about the nuisance parameter
    row = []

    flag = False
    mean_p, sigma_p, sigma_pu, sigma_pd = 0, 0, 0, 0

    if nuis_p == None:
        # nuisance parameter NOT present in the prefit result
        if not options.absolute_values and not (options.pullDef == "unconstPullAsym"):
            continue
        row += ["[%.2f, %.2f]" % (nuis_s.getMin(), nuis_s.getMax())]

    else:
        # get best-fit value and uncertainty at prefit for this
        # nuisance parameter
        if nuis_p.getErrorLo() == 0:
            nuis_p.setError(nuis_p.getErrorHi())
        mean_p, sigma_p, sigma_pu, sigma_pd = (
            nuis_p.getVal(),
            nuis_p.getError(),
            nuis_p.getErrorHi(),
            nuis_p.getErrorLo(),
        )

        if not sigma_p > 0:
            sigma_p = (nuis_p.getMax() - nuis_p.getMin()) / 2
        nuisIsSymm = abs(abs(nuis_p.getErrorLo()) - abs(nuis_p.getErrorHi())) < 0.01 or nuis_p.getErrorLo() == 0
        if options.absolute_values:
            if nuisIsSymm:
                row += ["%.6f +/- %.6f" % (nuis_p.getVal(), nuis_p.getError())]
            else:
                row += ["%.6f +%.6f %.6f" % (nuis_p.getVal(), nuis_p.getErrorHi(), nuis_p.getErrorLo())]

    for fit_name, nuis_x in [("b", nuis_b), ("s", nuis_s)]:
        if nuis_x == None:
            row += [" n/a "]
        else:
            nuisIsSymm = abs(abs(nuis_x.getErrorLo()) - abs(nuis_x.getErrorHi())) < 0.01 or nuis_x.getErrorLo() == 0
            if nuisIsSymm:
                nuis_x.setError(nuis_x.getErrorHi())
            nuiselo = abs(nuis_x.getErrorLo()) if nuis_x.getErrorLo() > 0 else nuis_x.getError()
            nuisehi = nuis_x.getErrorHi()
            if options.pullDef and nuis_p != None:
                nx, ned, neu = CP.returnPullAsym(
                    options.pullDef,
                    nuis_x.getVal(),
                    mean_p,
                    nuisehi,
                    sigma_pu,
                    abs(nuiselo),
                    abs(sigma_pd),
                )
            else:
                nx, ned, neu = nuis_x.getVal(), nuiselo, nuisehi

            if nuisIsSymm:
                row += ["%+.2f +/- %.2f" % (nx, (abs(ned) + abs(neu)) / 2)]
            else:
                row += ["%+.2f +%.2f %.2f" % (nx, neu, ned)]

            if options.workspace:
                if fit_name == "b":
                    pdf = workspace.pdf(name + "_Pdf")
                    var = workspace.var(name)
                    var_val = var.getVal()
                    var.setVal(nuis_x.getVal())
                    bfit_nll = -pdf.getLogVal(ROOT.RooArgSet(var))
                    var.setVal(var_val)

                if options.workspace:
                    var.setVal(nuis_x.getVal())
                    sfit_nll = -pdf.getLogVal(ROOT.RooArgSet(var))
                    var.setVal(var_val)

            if nuis_p != None:
                if options.plotfile:
                    if fit_name == "b":
                        nuis_p_i += 1
                        hist_idx = (nuis_p_i - 1) // options.max_nuis
                        bin_idx = ((nuis_p_i - 1) % options.max_nuis) + 1
                        if options.pullDef and nuis_p != None:
                            # nx,ned,neu = CP.returnPullAsym(options.pullDef,nuis_x.getVal(),mean_p,nuis_x.getErrorHi(),sigma_pu,abs(nuis_x.getErrorLo()),abs(sigma_pd))
                            gr_fit_b[hist_idx].SetPoint(bin_idx - 1, bin_idx - 0.5 + 0.1, nx)
                            gr_fit_b[hist_idx].SetPointError(bin_idx - 1, 0, 0, ned, neu)
                        else:
                            gr_fit_b[hist_idx].SetPoint(bin_idx - 1, bin_idx - 0.5 + 0.1, nuis_x.getVal())
                            gr_fit_b[hist_idx].SetPointError(
                                bin_idx - 1,
                                0,
                                0,
                                abs(nuis_x.getErrorLo()),
                                nuis_x.getErrorHi(),
                            )
                        hist_fit_b[hist_idx].SetBinContent(bin_idx, nuis_x.getVal())
                        hist_fit_b[hist_idx].SetBinError(bin_idx, nuis_x.getError())
                        hist_fit_b[hist_idx].GetXaxis().SetBinLabel(bin_idx, name)
                        gr_fit_b[hist_idx].GetXaxis().SetBinLabel(bin_idx, name)
                    if fit_name == "s":
                        if options.pullDef and nuis_p != None:
                            # nx,ned,neu = CP.returnPullAsym(options.pullDef,nuis_x.getVal(),mean_p,nuis_x.getErrorHi(),sigma_pu,abs(nuis_x.getErrorLo()),abs(sigma_pd))
                            gr_fit_s[hist_idx].SetPoint(bin_idx - 1, bin_idx - 0.5 - 0.1, nx)
                            gr_fit_s[hist_idx].SetPointError(bin_idx - 1, 0, 0, ned, neu)
                        else:
                            gr_fit_s[hist_idx].SetPoint(bin_idx - 1, bin_idx - 0.5 - 0.1, nuis_x.getVal())
                            gr_fit_s[hist_idx].SetPointError(
                                bin_idx - 1,
                                0,
                                0,
                                abs(nuis_x.getErrorLo()),
                                nuis_x.getErrorHi(),
                            )
                        hist_fit_s[hist_idx].SetBinContent(bin_idx, nuis_x.getVal())
                        hist_fit_s[hist_idx].SetBinError(bin_idx, nuis_x.getError())
                        hist_fit_s[hist_idx].GetXaxis().SetBinLabel(bin_idx, name)
                        gr_fit_s[hist_idx].GetXaxis().SetBinLabel(bin_idx, name)
                    hist_prefit[hist_idx].SetBinContent(bin_idx, mean_p)
                    hist_prefit[hist_idx].SetBinError(bin_idx, sigma_p)
                    hist_prefit[hist_idx].GetXaxis().SetBinLabel(bin_idx, name)

                if sigma_p > 0:
                    if options.pullDef:
                        valShift = nx
                        sigShift = 1
                    else:
                        # calculate the difference of the nuisance parameter
                        # w.r.t to the prefit value in terms of the uncertainty
                        # on the prefit value
                        valShift = (nuis_x.getVal() - mean_p) / sigma_p

                        # ratio of the nuisance parameter's uncertainty
                        # w.r.t the prefit uncertainty
                        sigShift = nuis_x.getError() / sigma_p

                else:
                    # print "No definition for prefit uncertainty %s. Printing absolute shifts"%(nuis_p.GetName())
                    valShift = nuis_x.getVal() - mean_p
                    sigShift = nuis_x.getError()

                if options.pullDef:
                    row[-1] = ""
                elif options.absolute_values:
                    row[-1] = " (%+4.2fsig, %4.2f)" % (valShift, sigShift)
                else:
                    row[-1] = " %+4.2f, %4.2f" % (valShift, sigShift)

                if fit_name == "b":
                    pulls.append(valShift)

                if abs(valShift) > options.vtol2 or abs(sigShift - 1) > options.stol2:
                    # severely report this nuisance:
                    #
                    # the best fit moved by more than 2.0 sigma or the uncertainty (sigma)
                    # changed by more than 50% (default thresholds) w.r.t the prefit values

                    isFlagged[(name, fit_name)] = 2

                    flag = True

                elif abs(valShift) > options.vtol or abs(sigShift - 1) > options.stol:
                    # report this nuisance:
                    #
                    # the best fit moved by more than 0.3 sigma or the uncertainty (sigma)
                    # changed by more than 10% (default thresholds) w.r.t the prefit values

                    if options.show_all_parameters:
                        isFlagged[(name, fit_name)] = 1

                    flag = True

                elif options.show_all_parameters:
                    flag = True

    # end of loop over s and b

    row += ["%+4.2f" % fit_s.correlation(name, options.poi)]
    row += ["%+4.3f" % (nuis_x.getError() * fit_s.correlation(name, options.poi) * error_poi)]
    if options.workspace:
        dnll = bfit_nll - sfit_nll
        dnlls.append((name, dnll))
        row += ["%.4f" % dnll]
    if flag or options.show_all_parameters:
        table[name] = row

# end of loop over all fitted parameters

#fill dnll and cumulative dnll plots
if options.plotfile and options.workspace:
    len_dnll = len(dnlls)
    hist_dnll = []
    hist_cdnll = []
    for hist_idx in range(((len_dnll - 1) // options.max_nuis) + 1):
        nbins = min(len_dnll, options.max_nuis, len_dnll - options.max_nuis * hist_idx)
        hist_dnll += [ROOT.TH1F("dnll %s" % hist_idx, "delta log-likelihoods   ;;%s %s" % (title, hist_idx), nbins, 0, nbins)]
        hist_cdnll += [ROOT.TH1F("cdnll %s" % hist_idx, "cumulative delta log-likelihoods   ;;%s %s" % (title, hist_idx), nbins, 0, nbins)]
    dnlls.sort(key=lambda x: -x[1])
    cdnll = 0
    for idx, (nm, val) in enumerate(dnlls):
        hist_idx = idx // options.max_nuis
        bin_idx = idx % options.max_nuis
        hist_dnll[hist_idx].SetBinContent(bin_idx + 1, val)
        hist_dnll[hist_idx].GetXaxis().SetBinLabel(bin_idx + 1, nm)
        cdnll += val
        hist_cdnll[hist_idx].SetBinContent(bin_idx + 1, cdnll)

# ----------
# print the results
# ----------

# print details
print(setUpString)
print()

fmtstring = "%-40s     %15s    %15s  %10s  %10s"
highlight = "*%s*"
morelight = "!%s!"
pmsub, sigsub = None, None
if options.format == "text":
    if options.skipFitS:
        print(" option '--skipFitS' set true. s+b Fit is just a copy of the b-only fit")
    if options.skipFitB:
        print(" option '--skipFitB' set true. b-only Fit is just a copy of the s+b fit")
    if options.pullDef:
        fmtstring = "%-40s       %30s    %30s  %10s  %10s"
        headers = ["name", "b-only fit pull", "s+b fit pull", "rho", "approx impact"]
    elif options.absolute_values:
        fmtstring = "%-40s     %15s    %30s    %30s  %10s  %10s"
        headers = ["name", "pre fit", "b-only fit", "s+b fit", "rho", "approx impact"]
    else:
        headers = ["name", "b-only fit", "s+b fit", "rho", "approx impact"]
    if options.workspace:
        fmtstring = fmtstring + " %10s"
        headers += ["dnll"]
    print(fmtstring % tuple(headers))

elif options.format == "latex":
    pmsub = (r"(\S+) \+/- (\S+)", r"$\1 \\pm \2$")
    sigsub = ("sig", r"$\\sigma$")
    highlight = "\\textbf{%s}"
    morelight = "{{\\color{red}\\textbf{%s}}}"
    headers_first = None
    if options.skipFitS:
        print(" option '--skipFitS' set true. $s+b$ Fit is just a copy of the $b$-only fit")
    if options.skipFitB:
        print(" option '--skipFitB' set true. $b$-only Fit is just a copy of the $s+b$ fit")
    if options.pullDef:
        fmtstring = "%-40s & %30s & %30s & %6s & %6s  "
        tab_header = "\\begin{tabular}{|l|r|r|r|r|"
        headers = ["name", "$b$-only fit pull", "$s+b$ fit pull", r"$\rho(\theta, \mu)$", r"I(\theta, \mu)"]
    elif options.absolute_values:
        fmtstring = "%-40s &  %15s & %30s & %30s & %6s & %6s "
        tab_header = "\\begin{tabular}{|l|r|r|r|r|r|"
        headers = ["name", "pre fit", "$b$-only fit pull", "$s+b$ fit pull", r"$\rho(\theta, \mu)$", r"I(\theta, \mu)"]
    else:
        fmtstring = "%-40s &  %15s & %15s & %6s & %6s "
        tab_header = "\\begin{tabular}{|l|r|r|r|r|"
        # what = r"$(x_\text{out} - x_\text{in})/\sigma_{\text{in}}$, $\sigma_{\text{out}}/\sigma_{\text{in}}$"
        what = r"\Delta x/\sigma_{\text{in}}$, $\sigma_{\text{out}}/\sigma_{\text{in}}$"
        headers_first = ["", "$b$-only fit", "$s+b$ fit", "", ""]
        headers = ["name", what, what, r"$\rho(\theta, \mu)$", r"I(\theta, \mu)"]
    if options.workspace:
        tab_header += "r|"
        fmtstring += " & %6s "
        if headers_first is not None:
            headers_first += [""]
        headers += [r"\Delta NLL"]
    fmtstring += " \\\\"
    print(tab_header + "} \\hline ")
    if headers_first is not None:
        print(fmtstring % tuple(headers_first))
    print(fmtstring % tuple(headers), " \\hline")

elif options.format == "twiki":
    pmsub = (r"(\S+) \+/- (\S+)", r"\1 &plusmn; \2")
    sigsub = ("sig", r"&sigma;")
    highlight = "<b>%s</b>"
    morelight = "<b style='color:red;'>%s</b>"
    if options.skipFitS:
        print(" option '--skipFitS' set true. $s+b$ Fit is just a copy of the $b$-only fit")
    if options.skipFitB:
        print(" option '--skipFitB' set true. $b$-only Fit is just a copy of the $s+b$ fit")
    if options.pullDef:
        fmtstring = "| <verbatim>%-40s</verbatim>  | %-30s  | %-30s   | %-15s  | %-15s  | %-15s  |"
        header = "| *name* | *b-only fit pull* | *s+b fit pull* | *corr.* | *approx. impact* |"
    elif options.absolute_values:
        fmtstring = "| <verbatim>%-40s</verbatim>  | %-15s  | %-30s  | %-30s   | %-15s  | %-15s  |"
        header = "| *name* | *pre fit* | *b-only fit* | *s+b fit* | *corr.* | *approx. impact* |"
    else:
        fmtstring = "| <verbatim>%-40s</verbatim>  | %-15s  | %-15s | %-15s  | %-15s  |"
        header = "| *name* | *b-only fit* | *s+b fit* | *corr.* | *approx. impact* |"
    if options.workspace:
        fmtstring += " %-15s  |"
        header += " *delta nll* |"
    print(header)

elif options.format == "html":
    pmsub = (r"(\S+) \+/- (\S+)", r"\1 &plusmn; \2")
    sigsub = ("sig", r"&sigma;")
    highlight = "<b>%s</b>"
    morelight = "<strong>%s</strong>"
    print(
        """
<html><head><title>Comparison of nuisances</title>
<style type="text/css">
    td, th { border-bottom: 1px solid black; padding: 1px 1em; }
    td { font-family: 'Consolas', 'Courier New', courier, monospace; }
    strong { color: red; font-weight: bolder; }
</style>
</head><body style="font-family: 'Verdana', sans-serif; font-size: 10pt;"><h1>Comparison of nuisances</h1>
<table>
"""
    )
    if options.pullDef:
        header = "<tr><th>nuisance</th><th>background fit pull </th><th>signal fit pull</th><th>&rho;(&mu;, &theta;)</th><th>I(&mu;, &theta;)</th>"
        fmtstring = "<tr><td><tt>%-40s</tt> </td><td> %-30s </td><td> %-30s </td><td> %-15s </td><td> %-15s </td></tr>"
    elif options.absolute_values:
        header = "<tr><th>nuisance</th><th>pre fit</th><th>background fit </th><th>signal fit</th><th>correlation</th>"
        fmtstring = "<tr><td><tt>%-40s</tt> </td><td> %-15s </td><td> %-30s </td><td> %-30s </td><td> %-15s </td><td> %-15s </td>"
    else:
        what = "&Delta;x/&sigma;<sub>in</sub>, &sigma;<sub>out</sub>/&sigma;<sub>in</sub>"
        header = "<tr><th>nuisance</th><th>background fit<br/>%s </th><th>signal fit<br/>%s</th><th>&rho;(&mu;, &theta;)<th>I(&mu;, &theta;)</th>" % (
            what,
            what,
        )
        fmtstring = "<tr><td><tt>%-40s</tt> </td><td> %-15s </td><td> %-15s </td><td> %-15s </td><td> %-15s </td>"
    if options.workspace:
        header += "<th>&Delta;NLL</th></tr>"
        fmtstring += "<td> %-15s </td>"
    header += "</tr>"
    print(header)
    fmtstring += "</tr>"

names = list(table.keys())
names.sort()
rho_idx = -2 if not options.workspace else -3
imp_idx = -1 if not options.workspace else -2
if options.sortBy == "correlation":
    names = [[abs(float(table[t][rho_idx])), t] for t in table.keys()]
    names.sort()
    names.reverse()
    names = [n[1] for n in names]
elif options.sortBy == "impact":
    names = [[abs(float(table[t][imp_idx])), t] for t in table.keys()]
    names.sort()
    names.reverse()
    names = [n[1] for n in names]
elif options.sortBy == "dnll":
    names = [[float(table[t][-1]), t] for t in table.keys()]
    names.sort()
    names.reverse()
    names = [n[1] for n in names]

highlighters = {1: highlight, 2: morelight}
fl_b_idx = -4 if not options.workspace else -5
fl_s_idx = -3 if not options.workspace else -4
for n in names:
    v = table[n]
    if pmsub != None:
        v = [re.sub(pmsub[0], pmsub[1], i) for i in v]
    if sigsub != None:
        v = [re.sub(sigsub[0], sigsub[1], i) for i in v]
    if (n, "b") in isFlagged:
        v[fl_b_idx] = highlighters[isFlagged[(n, "b")]] % v[fl_b_idx]
    if (n, "s") in isFlagged:
        v[fl_s_idx] = highlighters[isFlagged[(n, "s")]] % v[fl_s_idx]
    if options.format == "latex":
        n = n.replace(r"_", r"\_")

    j = [n] + v
    print(fmtstring % tuple(j))

if options.format == "latex":
    print(" \\hline\n\\end{tabular}")
elif options.format == "html":
    print("</table></body></html>")


if options.plotfile:
    import ROOT

    fout = ROOT.TFile(options.plotfile, "RECREATE")
    ROOT.gROOT.SetStyle("Plain")
    ROOT.gStyle.SetOptFit(1)
    ROOT.gStyle.SetPadBottomMargin(0.3)
    histogram = ROOT.TH1F("pulls", "Pulls", 60, -3, 3)
    for pull in pulls:
        histogram.Fill(pull)
    canvas = ROOT.TCanvas("asdf", "asdf", 800, 800)
    if options.pullDef:
        histogram.GetXaxis().SetTitle("pull")
    else:
        histogram.GetXaxis().SetTitle("(#theta-#theta_{0})/#sigma_{pre-fit}")
    histogram.SetTitle("Post-fit nuisance pull distribution")
    histogram.SetMarkerStyle(20)
    histogram.SetMarkerSize(2)
    histogram.Draw("pe")
    fout.WriteTObject(canvas)

    for idx in range(len(hist_fit_s)):
        canvas_nuis = ROOT.TCanvas("nuisances_%s" % idx, "nuisances_%s" % idx, 900, 600)
        hist_fit_e_s = hist_fit_s[idx].Clone("errors_s %s" % idx)
        hist_fit_e_b = hist_fit_b[idx].Clone("errors_b %s" % idx)
        # gr_fit_s = getGraph(hist_fit_s,-0.1)
        # gr_fit_b = getGraph(hist_fit_b, 0.1)
        gr_fit_s[idx].SetLineColor(ROOT.kRed)
        gr_fit_s[idx].SetMarkerColor(ROOT.kRed)
        gr_fit_b[idx].SetLineColor(ROOT.kBlue)
        gr_fit_b[idx].SetMarkerColor(ROOT.kBlue)
        gr_fit_b[idx].SetMarkerStyle(20)
        gr_fit_s[idx].SetMarkerStyle(20)
        gr_fit_b[idx].SetMarkerSize(1.0)
        gr_fit_s[idx].SetMarkerSize(1.0)
        gr_fit_b[idx].SetLineWidth(2)
        gr_fit_s[idx].SetLineWidth(2)
        hist_prefit[idx].SetLineWidth(2)
        hist_prefit[idx].SetTitle("Nuisance Paramaeters")
        hist_prefit[idx].SetLineColor(ROOT.kBlack)
        hist_prefit[idx].SetFillColor(ROOT.kGray)
        hist_prefit[idx].SetMaximum(3)
        hist_prefit[idx].SetMinimum(-3)
        hist_prefit[idx].Draw("E2")
        hist_prefit[idx].Draw("histsame")
        gr_fit_b[idx].Draw("EPsame")
        gr_fit_s[idx].Draw("EPsame")
        canvas_nuis.SetGridx()
        canvas_nuis.RedrawAxis()
        canvas_nuis.RedrawAxis("g")
        leg = ROOT.TLegend(0.6, 0.7, 0.89, 0.89)
        leg.SetFillColor(0)
        leg.SetTextFont(42)
        leg.AddEntry(hist_prefit[idx], "Prefit", "FL")
        leg.AddEntry(gr_fit_b[idx], "B-only fit", "EPL")
        leg.AddEntry(gr_fit_s[idx], "S+B fit", "EPL")
        leg.Draw()
        fout.WriteTObject(canvas_nuis)

        canvas_pferrs = ROOT.TCanvas("post_fit_errs_%s" % idx, "post_fit_errs_%s" % idx, 900, 600)
        for b in range(1, hist_fit_e_s.GetNbinsX() + 1):
            hist_fit_e_s.SetBinContent(b, hist_fit_s[idx].GetBinError(b) / hist_prefit[idx].GetBinError(b))
            hist_fit_e_b.SetBinContent(b, hist_fit_b[idx].GetBinError(b) / hist_prefit[idx].GetBinError(b))
            hist_fit_e_s.SetBinError(b, 0)
            hist_fit_e_b.SetBinError(b, 0)
        hist_fit_e_s.SetFillColor(ROOT.kRed)
        hist_fit_e_b.SetFillColor(ROOT.kBlue)
        hist_fit_e_s.SetBarWidth(0.4)
        hist_fit_e_b.SetBarWidth(0.4)
        hist_fit_e_b.SetBarOffset(0.45)
        hist_fit_e_b.GetYaxis().SetTitle("#sigma_{#theta}/(#sigma_{#theta} prefit)")
        hist_fit_e_b.SetTitle("Nuisance Parameter Uncertainty Reduction")
        hist_fit_e_b.SetMaximum(1.5)
        hist_fit_e_b.SetMinimum(0)
        hist_fit_e_b.Draw("bar")
        hist_fit_e_s.Draw("barsame")
        leg_rat = ROOT.TLegend(0.6, 0.7, 0.89, 0.89)
        leg_rat.SetFillColor(0)
        leg_rat.SetTextFont(42)
        leg_rat.AddEntry(hist_fit_e_b, "B-only fit", "F")
        leg_rat.AddEntry(hist_fit_e_s, "S+B fit", "F")
        leg_rat.Draw()
        line_one = ROOT.TLine(0, 1, hist_fit_e_s.GetXaxis().GetXmax(), 1)
        line_one.SetLineColor(1)
        line_one.SetLineStyle(2)
        line_one.SetLineWidth(2)
        line_one.Draw()
        canvas_pferrs.RedrawAxis()

        fout.WriteTObject(canvas_pferrs)

        if options.workspace:
            canvas_dnll = ROOT.TCanvas("dnlls_%s" % idx, "dnlls_%s" % idx, 900, 600)
            hist_dnll[idx].SetStats(0)
            hist_dnll[idx].SetLineWidth(2)
            hist_dnll[idx].SetTitle("Nuisance Parameters")
            hist_dnll[idx].SetLineColor(ROOT.kBlack)
            hist_dnll[idx].SetFillColor(ROOT.kGray)
            hist_dnll[idx].SetMaximum(2)
            hist_dnll[idx].SetMinimum(-1)
            hist_dnll[idx].GetYaxis().SetTitle("NLL(fit_{b})  - NLL(fit_{s+b})")
            hist_dnll[idx].Draw()

            hist_cdnll[idx].SetLineWidth(2)
            hist_cdnll[idx].SetLineColor(ROOT.kBlue)
            hist_cdnll[idx].Draw("same")
            canvas_dnll.SetGridx()
            canvas_dnll.RedrawAxis()
            canvas_dnll.RedrawAxis("g")
            leg = ROOT.TLegend(0.6, 0.7, 0.89, 0.89)
            leg.SetFillColor(0)
            leg.SetTextFont(42)
            leg.AddEntry(hist_dnll[idx], "individual nuisance", "FL")
            leg.AddEntry(hist_cdnll[idx], "cumulative", "FL")
            leg.Draw()
            latex = ROOT.TLatex()
            posx = 4 if hist_dnll[idx].GetNbinsX() > 10 else 0.5
            latex.DrawLatex(posx, 1.5, "Total #Delta NLL %.3f" % (cdnll))
            fout.WriteTObject(canvas_dnll)
