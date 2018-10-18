from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.http import FileResponse
import os
import tempfile
import libplot
import pandas as pd
import numpy as np
import libhttp
import sys

from violin import settings

def tmp_name():
    return next(tempfile._get_candidate_names())

def about(request):
    return JsonResponse({'name':'violin','version':'1.0','copyright':'Copyright (C) 2018 Antony Holmes'}, safe=False)

def handle_uploaded_file(f):
    
    out, path = tempfile.mkstemp(dir=settings.TMP_DIR)
    
    with open(out, 'wb') as writer:
        for chunk in f.chunks():
            writer.write(chunk)
            
    return path
            
def format_axes(ax, x='Category', y='Value'):
    libplot.format_axes(ax, x=x, y=y)
    ax.tick_params(axis='x', which='minor', bottom=False)
    

def plot(file, color_file, violin=True, box=False, swarm=False, x='Category', y='Value'):
    f, out = tempfile.mkstemp(suffix='.pdf', dir=settings.TMP_DIR)
    print(out)
    os.close(f)
    
    libplot.setup()
    
    #print(file, color_file, out)

    df = pd.read_csv(file, sep='\t', header=0)

    df_color = pd.read_csv(color_file, sep='\t', header=0)

    colors=df_color['Color'].tolist()

    w = np.unique(df['Label']).size  * settings.COLUMN_WIDTH

    fig = libplot.new_base_fig(w=w, h=settings.PLOT_HEIGHT)

    if violin:
        ax = libplot.new_ax(fig)
        
        if box or swarm:
            tint = 0.5
        else:
            tint = 0
            
        libplot.violinplot(df, x='Label', y='Value', colors=colors, width=0.8, tint=tint, ax=ax)

        format_axes(ax, x=x, y=y)

    if box:
        if violin:
            ax2 = libplot.new_ax(fig, sharex=ax, sharey=ax, zorder=10)
            ax2.patch.set_alpha(0)
        else:
           ax2 = libplot.new_ax(fig)

        if swarm:
            tint = 0.8
        else:
            tint = 0
            
        libplot.boxplot(df, x='Label', y='Value', colors=colors, width=0.2, tint=tint, ax=ax2)
        
        if violin:
            libplot.invisible_axes(ax2)
        else:
            format_axes(ax2, x=x, y=y)
        

    if swarm:
        if violin or box:
            ax3 = libplot.new_ax(fig, sharex=ax, sharey=ax, zorder=100)
            ax3.patch.set_alpha(0)
        else:
            ax3 = libplot.new_ax(fig)
        
        libplot.swarmplot(df, x='Label', y='Value', colors=colors, ax=ax3)
        
        if violin or box:
            libplot.invisible_axes(ax3)
        else:
            format_axes(ax3, x=x, y=y)


    libplot.savefig(fig, out)
    
    return out

def pdf(request):
    #print(request)
    #print(request.body)
    
    id_map = libhttp.parse_params(request, {'violin':'t', 'box':'f', 'swarm':'f', 'x':'Category', 'y':'Value'})
    
    violin = id_map['violin'][0] == 't'
    box = id_map['box'][0] == 't'
    swarm = id_map['swarm'][0] == 't'
    x = id_map['x'][0]
    y = id_map['y'][0]
    
    if request.method != 'POST':
        return JsonResponse(['No POST'], safe=False)
    
    print('data_file' in request.FILES)
    
    if 'data_file' not in request.FILES:
        return JsonResponse(['No file'], safe=False)
        
    df = handle_uploaded_file(request.FILES['data_file'])
    
    if 'color_file' not in request.FILES:
        return JsonResponse(['No file'], safe=False)
        
    cf = handle_uploaded_file(request.FILES['color_file'])
    
    pf = plot(df, cf, violin=violin, box=box, swarm=swarm, x=x, y=y)
    
    os.remove(df)
    os.remove(cf)
    
    #return JsonResponse([d], safe=False)
    
    return FileResponse(open(pf, 'rb'), as_attachment=True, filename='violin.pdf')



