import matplotlib.pyplot as plt
import matplotlib.patches as patches

from matplotlib.lines import Line2D

import plotly.graph_objs as go
import plotly.express as px

from plotly.subplots import make_subplots

import streamlit as st

COLOR = 'white'
cmap = plt.get_cmap('tab10')

XMAX, XMIN = 120, 0
YMAX, YMIN = 80, 0

color_list = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b','#e377c2','#7f7f7f','#bcbd22','#17becf']

def vizualize_shot_points(df_tmp, teams_df, players_df, matchPeriod_list, library):
    if library == 'matplotlib':
        fig, axes = draw_pitches_matplotlib(nrows=len(matchPeriod_list), ncols=2)
        for i, (matchPeriod, teamId) in enumerate(df_tmp[['matchPeriod', 'teamId']].drop_duplicates().sort_values(by=['teamId', 'matchPeriod']).values.tolist()):
            ax = axes.reshape([-1, 2])[int(i/2), i%2]
            team_name = teams_df[teams_df.wyId==teamId].name.values[0]
            ax.set_title(f'{matchPeriod} {team_name}', color='white')
            
            for (positions, tags) in df_tmp[(df_tmp.matchPeriod==matchPeriod)&(df_tmp.teamId==teamId)][['positions', 'tags']].values.tolist():
                id_list = [tag_dict['id'] for tag_dict in tags]
            
                st_x, st_y = XMAX * positions[0]['x'] / 100, YMAX * (1 - positions[0]['y'] / 100)
                
                ax.scatter(x=st_x, y=st_y, c = cmap(1) if 101 in id_list else cmap(0), label='success' if 101 in id_list else 'fail')

            if i == len(matchPeriod_list)*2-1:
                ax.legend([Line2D([0], [0], color=cmap(j)) for j in range(2)], ['success', 'failure'], loc='lower right')

        st.pyplot(fig, facecolor=fig.get_facecolor(), bbox_inches = 'tight')

    else:
        title_list = [f'{matchPeriod} {teams_df[teams_df.wyId==teamId].name.values[0]}' for [matchPeriod, teamId] in df_tmp[['matchPeriod', 'teamId']].drop_duplicates().sort_values(by=['teamId', 'matchPeriod']).values.tolist()]
        fig = draw_pitches_plotly(len(matchPeriod_list), 2, title_list)

        df_tmp['x'] = None
        df_tmp['y'] = None
        df_tmp[['x', 'y']] = df_tmp.apply(lambda xs: [XMAX*xs['positions'][0]['x']/100, YMAX*(1-xs['positions'][0]['y']/100)], result_type='expand', axis=1)

        df_tmp['result'] = df_tmp.apply(lambda xs: 'success' if 101 in [tag['id'] for tag in xs['tags']] else 'failure', axis=1)

        df_tmp['name'] = df_tmp.apply(lambda xs: 'player= '+players_df[players_df.wyId==xs['playerId']].shortName.tolist()[0]+'\n time= '+str(int(xs['eventSec']/60))+'m'+str(int(xs['eventSec']%60))+'s\n result= '+xs['result'], axis=1)

        legend_dict = {'success':0, 'failure':0}
        for i, (matchPeriod, teamId) in enumerate(df_tmp[['matchPeriod', 'teamId']].drop_duplicates().sort_values(by=['teamId', 'matchPeriod']).values.tolist()):
            i, j = int(i/2)+1, i%2+1
            for result in df_tmp[(df_tmp.matchPeriod==matchPeriod)&(df_tmp.teamId==teamId)].result.unique().tolist():
                fig.add_trace(
                    go.Scatter(
                        x=df_tmp[(df_tmp.matchPeriod==matchPeriod)&(df_tmp.teamId==teamId)&(df_tmp.result==result)].x.tolist()
                        , y=df_tmp[(df_tmp.matchPeriod==matchPeriod)&(df_tmp.teamId==teamId)&(df_tmp.result==result)].y.tolist()
                        , name=result
                        , mode='markers'
                        , marker=dict(color='orange' if result=='success' else 'skyblue')
                        , hovertext=df_tmp[(df_tmp.matchPeriod==matchPeriod)&(df_tmp.teamId==teamId)&(df_tmp.result==result)].name.tolist()
                        , showlegend= legend_dict[result] == 0
                    )
                    , row=i, col=j)
                legend_dict[result] += 1

        st.plotly_chart(fig)

def visualize_pass_lines(df_tmp, teams_df, players_df, subEventName_list, matchPeriod_list, library):
    if library == 'matplotlib':
        df_tmp['minute'] = df_tmp.eventSec.apply(lambda x: int(x/60))
        st_minute, ed_minute = st.slider('select displaying range', 0, 45, [0, 45], 1)
        df_tmp = df_tmp[(st_minute<=df_tmp.minute)&(df_tmp.minute<=ed_minute)]

        fig, axes = draw_pitches_matplotlib(nrows=len(matchPeriod_list), ncols=2)
        N = len(df_tmp)
        cnt = 0
        with st.spinner('Wait for it ...'):
            my_bar = st.progress(cnt)
            for i, (matchPeriod, teamId) in enumerate(df_tmp[['matchPeriod', 'teamId']].drop_duplicates().sort_values(by=['teamId', 'matchPeriod']).values.tolist()):
                ax = axes.reshape([-1, 2])[int(i/2), i%2]
                team_name = teams_df[teams_df.wyId==teamId].name.values[0]
                ax.set_title(f'{matchPeriod} {team_name}', color='white')

                for (positions, subEventName, tags) in df_tmp[(df_tmp.eventName=='Pass')&(df_tmp.matchPeriod==matchPeriod)&(df_tmp.teamId==teamId)][['positions', 'subEventName', 'tags']].values.tolist():
                    my_bar.progress(int((cnt+1)/N*100))

                    ed_x, ed_y = XMAX * positions[1]['x'] / 100, YMAX * (1 - positions[1]['y'] / 100)
                    st_x, st_y = XMAX * positions[0]['x'] / 100, YMAX * (1 - positions[0]['y'] / 100)
                    id_list = [tag_dict['id'] for tag_dict in tags]

                    ax.annotate('', xy=[ed_x, ed_y], xytext=[st_x, st_y],
                            arrowprops=dict(shrink=0, width=0.5, headwidth=4, alpha=0.8,
                                            headlength=5, connectionstyle='arc3',
                                            facecolor=cmap(subEventName_list.index(subEventName)), edgecolor=cmap(subEventName_list.index(subEventName))
                                            , linestyle= 'solid' if 1801 in id_list else 'dashed'
                                           )

                           )

                    cnt += 1

                for positions in df_tmp[(df_tmp.eventName=='Interruption')&(df_tmp.matchPeriod==matchPeriod)&(df_tmp.teamId==teamId)]['positions'].values.tolist():
                    st_x, st_y = XMAX * positions[0]['x'] / 100, YMAX * (1 - positions[0]['y'] / 100)
                    ax.scatter(x=st_x, y=st_y, c='white', s=100, marker='x')


                if i == len(matchPeriod_list)*2-1:
                    ax.legend([Line2D([0], [0], color=cmap(j)) for j in range(len(subEventName_list))], subEventName_list, loc='lower right')

        st.success("Done!!")
        st.pyplot(fig, facecolor=fig.get_facecolor(), bbox_inches = 'tight')

    else:
        df_tmp['st_x'] = None
        df_tmp['st_y'] = None
        df_tmp['ed_x'] = None
        df_tmp['ed_y'] = None

        df_tmp[['st_x', 'st_y', 'ed_x', 'ed_y']] = df_tmp.apply(lambda xs: [XMAX*xs['positions'][0]['x']/100, YMAX*(1-xs['positions'][0]['y']/100), XMAX*xs['positions'][1]['x']/100, YMAX*(1-xs['positions'][1]['y']/100)], result_type='expand', axis=1)

        df_tmp['result'] = df_tmp.apply(lambda xs: 'success' if 1801 in [tag['id'] for tag in xs['tags']] else 'failure', axis=1)
        df_tmp['name'] = df_tmp.apply(lambda xs: 'player= '+players_df[players_df.wyId==xs['playerId']].shortName.tolist()[0]+'\n time= '+str(int(xs['eventSec']/60))+'m'+str(int(xs['eventSec']%60))+'s\n subEventName= '+xs['subEventName']+'\n result= '+xs['result'], axis=1)
        
        legend_dict = dict(zip(subEventName_list, [0]*len(subEventName_list)))
        color_dict = dict(zip(subEventName_list, color_list[:len(subEventName_list)]))
        title_list = [f'{matchPeriod} {teams_df[teams_df.wyId==teamId].name.values[0]}' for (matchPeriod, teamId) in df_tmp[['matchPeriod', 'teamId']].drop_duplicates().sort_values(by=['teamId', 'matchPeriod']).values.tolist()]

        fig = draw_pitches_plotly(len(matchPeriod_list), 2, title_list)
        N = len(df_tmp)
        cnt = 0
        with st.spinner('Wait for it ...'):
            my_bar = st.progress(cnt) 
            for i, (matchPeriod, teamId) in enumerate(df_tmp[['matchPeriod', 'teamId']].drop_duplicates().sort_values(by=['teamId', 'matchPeriod']).values.tolist()):
                i += 1
                
                for (st_x, st_y, ed_x, ed_y, subEventName, result, name) in df_tmp[(df_tmp.matchPeriod==matchPeriod)&(df_tmp.teamId==teamId)][['st_x', 'st_y', 'ed_x', 'ed_y', 'subEventName', 'result', 'name']].values.tolist():
                    my_bar.progress(int((cnt+1)/N*100))
                    
                    fig.add_annotation(go.layout.Annotation(
                        captureevents=True,
                        hovertext=name,
                        x=ed_x,
                        y=ed_y,
                        xref=f'x{i}',
                        yref=f'y{i}',
                        axref=f'x{i}',
                        ayref=f'y{i}',
                        ax=st_x,
                        ay=st_y,
                        arrowhead=4,
                        arrowsize=2,
                        arrowcolor=color_dict[subEventName],
                        showarrow=True,
            #             showlegend=legend_dict[subEventName] == 0
                    ))
                    
                    legend_dict[subEventName] += 1
                    cnt += 1
        st.success("Done!!")
        st.plotly_chart(fig)

def draw_pitches_matplotlib(nrows, ncols, colorbar=False):
    twitter_color = '#841d26'
    
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(10*ncols, 8*nrows if colorbar else 7*nrows), facecolor=twitter_color)
    
    fig.patch.set_facecolor('#141d26')
    
    for ax in axes.flatten():
        ax.patch.set_facecolor('#141d26')
        
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        

        ax.plot([0,120], [0, 0], color=COLOR)
        ax.plot([120,120], [0, 80], color=COLOR)
        ax.plot([120,0], [80,80], color=COLOR)
        ax.plot([0, 0], [80, 0], color=COLOR)
        ax.plot([60, 60], [0, 80], color=COLOR)
        ax.plot([0, 0], [36, 44], color=COLOR, linewidth=10)
        ax.plot([120, 120], [36, 44], color=COLOR, linewidth=10)

        centreCircle = plt.Circle((60, 40), 12, color=COLOR, fill=False)
        ax.add_patch(centreCircle)

        ax.plot([0, 18],  [18, 18], color=COLOR)
        ax.plot([18, 18],  [18, 62], color=COLOR)
        ax.plot([18, 0],  [62, 62], color=COLOR)
        ax.plot([0, 6],  [30, 30], color=COLOR)
        ax.plot([6, 6],  [30, 50], color=COLOR)
        ax.plot([6, 0],  [50, 50], color=COLOR)

        ax.plot([120, 102],  [18, 18], color=COLOR)
        ax.plot([102, 102],  [18, 62], color=COLOR)
        ax.plot([102, 120],  [62, 62], color=COLOR)
        ax.plot([120, 114],  [30, 30], color=COLOR)
        ax.plot([114, 114],  [30, 50], color=COLOR)
        ax.plot([114, 120],  [50, 50], color=COLOR)

        ax.tick_params(bottom=False, left=False, labelbottom=False, labelleft=False)

    return fig, axes

def draw_pitches_plotly(nrows, ncols, title_list=[], colorbar=False):
    twitter_color = 'rgb(20,29,38)'

    fig = make_subplots(rows=nrows, cols=ncols, subplot_titles=title_list, horizontal_spacing=0.05, vertical_spacing=0.05)
    for i in range(1,nrows+1):
        for j in range(1,ncols+1):
            
            line_list = [[[0,120], [0,0]], [[120,120], [0,80]], [[120,0], [80,80]], [[0,0], [80,0]], [[60,60], [0,80]]]
            line_list += [[[0,18], [18,18]], [[18,18], [18,62]], [[18,0], [62,62]], [[0,6], [30,30]], [[6,6], [30,50]], [[6,0], [50,50]]]
            line_list += [[[120, 102], [18,18]], [[102,102], [18,62]], [[102,120], [62,62]], [[120,114], [30,30]], [[114,114], [30,50]], [[114,120], [50,50]]]

            for [x, y] in line_list:
                fig.add_trace(go.Scatter(x=x, y=y,
                                    mode='lines',
                                    line=dict(color=COLOR, width=2.5),
                                    showlegend=False,
                                    hoverinfo='none'
                                    )
                             , row=i, col=j)

            line_list = [[[0,0], [36,44]], [[120,120], [36,44]]]
            for [x, y] in line_list:
                fig.add_trace(go.Scatter(x=x, y=y,
                                    mode='lines',
                                    line=dict(color=COLOR, width=12.5),
                                    showlegend=False,
                                    hoverinfo='none'
                                    )
                             , row=i, col=j)

            fig.add_shape(go.layout.Shape(type='circle', x0=60-12, y0=40-12, x1=60+12, y1=40+12, line_color=COLOR, line_width=2.5), row=i, col=j)
            fig.update_xaxes(range=[-1, 120+1], visible=False, row=i, col=j)
            fig.update_yaxes(range=[-1, 80+1], visible=False, row=i, col=j)
    
    fig.update_layout(go.Layout(width=3*150*ncols, height=2*150*nrows, plot_bgcolor=twitter_color, paper_bgcolor=twitter_color, autosize=True, margin=dict(l=10, r=10, t=20, b=10), legend=dict(font=dict(color=COLOR))))
    
    for i in fig['layout']['annotations']:
        i['font'] = dict(size=15,color=COLOR)
    
    return fig