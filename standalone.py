# -*- coding: utf-8 -*-
"""
Created on Mon Oct 10 10:59:17 2022

@author: Administrator
"""

from src.tindeq import TindeqProgressor
# from src.analysis import analyse_data

#%%
import time

from tornado.web import StaticFileHandler

from datetime import date

import pandas as pd
import glob
import numpy as np
import asyncio
import tornado
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.plotting import figure, ColumnDataSource, curdoc
from bokeh.layouts import row, column
from bokeh.models import Button, Slider, Div, Band, Whisker, Spinner, DataTable,TableColumn,DateFormatter

from bokeh.models import Button, CustomJS, PasswordInput, PreText, TextInput
from bokeh.io import export_png

from playsound import playsound
import threading

import os
import smtplib
import ssl
# import mimetypes
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.message import Message
from email.mime.base import MIMEBase
from email.mime.text  import MIMEText

#%%


class sound_thread(): 
    def __init__(self):
        self.running=False

    def start(self,soundfile,seconds):
        playsound(soundfile,block=False)
        self.running=True
        
        def sctn():  
           self.running=False 
        S = threading.Timer(seconds, sctn)  
        S.start()         
    # soundthread.start()
st = sound_thread()

class IdleState:
    bkg = 'orange'

    @staticmethod
    def update_cft(parent):
        parent.div.style['background-color'] = parent.state.bkg
        parent.div.text = '10:00'

    @staticmethod
    def end(parent):
        parent.state_start = time.time()
        parent.state = CountDownState


class CountDownState:
    bkg = 'orange'
    duration = 10

    @staticmethod
    def update_cft(parent):
        # count down timer
        elapsed = time.time() - parent.state_start
        remain = CountDownState.duration - elapsed
        fs = int(10 * (remain - int(remain))) *10
        secs = int(remain)
        parent.div.text = f"{secs:02d}:{fs:02d}"
        parent.div.style['background-color'] = parent.state.bkg
        if elapsed > CountDownState.duration:
            CountDownState.end(parent)
        if (remain<=3.5) & (st.running==False ):   
            st.start('tindeq_assessment/static/countdown.mp3',3.5)   
    @staticmethod
    def end(parent):
        parent.state_start = time.time()
        parent.state = GoState


class GoState:
    bkg = 'green'
    duration = 7

    @staticmethod
    def update_cft(parent):
        # count down timer
        elapsed = time.time() - parent.state_start
        remain = GoState.duration - elapsed
        fs = int(10 * (remain - int(remain))) *10
        secs = int(remain)
        parent.div.text = f"{secs:02d}:{fs:02d}"
        parent.div.style['background-color'] = parent.state.bkg
        if elapsed > GoState.duration:
            GoState.end(parent)
        if (remain<=1.1) & (remain>.5) & (st.running==False ):   
            st.start('tindeq_assessment/static/end.wav',1.1)
    @staticmethod
    def end(parent):
        parent.state_start = time.time()
        parent.state = RestState


class RestState:
    bkg = 'red'
    duration = 3

    @staticmethod
    def update_cft(parent):
        # count up timer
        # count down timer
        elapsed = time.time() - parent.state_start
        remain = RestState.duration - elapsed
        fs = int(10 * (remain - int(remain))) *10
        secs = int(remain)
        parent.div.text = f"{secs:02d}:{fs:02d}"
        parent.div.style['background-color'] = parent.state.bkg
        if elapsed > RestState.duration:
            RestState.end(parent)
        if (remain<=3.5) & (st.running==False ):   
            st.start('tindeq_assessment/static/countdown.mp3',3.5)   
    @staticmethod
    def end(parent):
        if parent.test_done:
            parent.state = IdleState
        else:
            parent.state_start = time.time()
            parent.state = GoState
            parent.reps -= 1


class CFT:
    def __init__(self):
        self.x = []
        self.y = []
        self.xnew = []
        self.ynew = []
        self.active = False
        self.duration = 240
        self.reps = 24
        self.state = IdleState
        self.test_done = False
        self.analysed = False
        self.tindeq = None
        # io_loop = tornado.ioloop.IOLoop.current()
        # io_loop.add_callback(connect, self)
        self.pwd = 'pw'
        self.maxtest_right=False 
        self.maxtest_left=False 
        self.max_right=0 
        self.max_left=0 
        self.rfd_right=0 
        self.rfd_left=0        
        self.cf_peak_load = 0
        self.cf_critical_load = 0   
        self.cf_x = []  
        self.cf_y = []  
         
    def log_force_sample(self, time, weight):
        if self.active:
            self.xnew.append(time)
            self.ynew.append(weight)
            self.x.append(time)
            self.y.append(weight)

    def reset(self):
        self.xnew, self.ynew = [], []
        
    
            
    def make_login(self, doc):
        
        self.x = []
        self.y = []
        self.xnew = []
        self.ynew = []
        self.active = False
        self.duration = 240
        self.reps = 24
        self.state = IdleState
        self.test_done = False
        self.analysed = False
        self.maxtest_right=False 
        self.maxtest_left=False 
        self.max_right=0 
        self.max_left=0 
        self.cf_peak_load = 0
        self.cf_critical_load = 0   
        self.cf_x = []  
        self.cf_y = []  
        self.seconds_left = 60*30       
       
        # password = PasswordInput(title="Password:")
        button = Button(label="Get started!")

        def verify():
            # if password.value==self.pwd:
                self.layout.children.pop()
                # self.layout.children.pop()
                self.make_document_choice(doc)    
                self.timout_t0=  time.time()
                # self.calback_timeout = self.doc.add_periodic_callback(self.check_for_timeout, 100)


        
        button.on_click(verify)
        
        
 
        # div_image = Div(text="""<img src="tindeq_assessment/static/Presentation1.gif" width = "800">""",min_height=400)
        # self.layout=column(password,button)
    
    
        self.layout=column(button)
        doc.add_root(self.layout)


    def make_gui(self,doc):
        self.make_login(doc)
        
    def make_document_email(self, doc):
        now = pd.to_datetime(date.today())
        # now = date.today()

     
        self.df=pd.DataFrame(columns=['datetime','Max strength left in kg','Max strength right in kg','Peak force in kg','Critical force in kg','RFD left in kg/s','RFD right in kg/s'])
        self.df.loc[0]=[now,self.max_left,self.max_right,self.cf_peak_load,self.cf_critical_load,self.rfd_left,self.rfd_right]
        self.df=self.df.replace(0,np.nan)
   
    
        # df=pd.DataFrame()
        # df['datetime']=now
        # df['max_left']=self.max_left
        # df['max_right']=self.max_right
        # df['peak_force']=self.cf_peak_load
        # df['max_left']=self.cf_critical_load
        # df['rfd_left']=self.rfd_left
        # df['rfd_right']=self.rfd_right
        
        Columns =[ TableColumn(field="datetime", title="Date", formatter=DateFormatter())]
        Columns= Columns + [TableColumn(field=Ci, title=Ci) for Ci in self.df.columns[1::]] # bokeh columns

        
        self.source_results=ColumnDataSource(self.df)

        self.data_table = DataTable(columns=Columns,source=self.source_results,index_position=None,height=100,auto_edit=True,sizing_mode='stretch_width')

        
        self.div_results = Div(text='',style={'font-size': '100%', 'color': 'black',                             
                              'text-align': 'left'})
        self.cf_percent=0


        # self.resultsource = ColumnDataSource(data=dict(x=self.cf_x, y=self.cf_y))
        # fig = figure( sizing_mode='stretch_both', x_axis_label='Seconds', y_axis_label='kg')
        # fig.line(x='x', y='y', source=self.resultsource)
        # self.resultsource = ColumnDataSource(data=dict([]))
        
        TOOLTIPS = [("Value", "$y")]
        
        fig1 = figure( title='Max. Strength',sizing_mode='stretch_both', y_axis_label='kg',x_axis_type='datetime',tooltips=TOOLTIPS)
        fig1.line(x='datetime', y='Max strength left in kg', source=self.source_results,color='red',legend_label="left")
        fig1.circle(x='datetime', y='Max strength left in kg', source=self.source_results,color='red',size=20)
        fig1.line(x='datetime', y='Max strength right in kg', source=self.source_results,color='blue',legend_label="right")
        fig1.circle(x='datetime', y='Max strength right in kg', source=self.source_results,color='blue',size=20)
        fig1.legend.location = "top_left"

        fig2 = figure( title='Peak force',sizing_mode='stretch_both', y_axis_label='kg',x_axis_type='datetime',tooltips=TOOLTIPS)
        fig2.line(x='datetime', y='Peak force in kg', source=self.source_results,color='red')
        fig2.circle(x='datetime', y='Peak force in kg', source=self.source_results,color='red',size=20)

        fig3 = figure( title='Critical force',sizing_mode='stretch_both', y_axis_label='kg',x_axis_type='datetime',tooltips=TOOLTIPS)
        fig3.line(x='datetime', y='Critical force in kg', source=self.source_results,color='red')
        fig3.circle(x='datetime', y='Critical force in kg', source=self.source_results,color='red',size=20)      
 
        fig4 = figure( title='Rate of force developmendt (RFD)',sizing_mode='stretch_both', y_axis_label='kg per s',x_axis_type='datetime',tooltips=TOOLTIPS)
        fig4.line(x='datetime', y='RFD left in kg/s', source=self.source_results,color='red',legend_label="left")
        fig4.circle(x='datetime', y='RFD left in kg/s', source=self.source_results,color='red',size=20)
        fig4.line(x='datetime', y='RFD right in kg/s', source=self.source_results,color='blue',legend_label="right")
        fig4.circle(x='datetime', y='RFD right in kg/s', source=self.source_results,color='blue',size=20)
        fig4.legend.location = "top_left"               
            
        self.text_input_mail = TextInput(value="", title="E-mail:")

        self.be1 = Button(label='Save results to database')
        def save_data():
            email = self.text_input_mail.value
            if len(email)>2 & ('@' in email) & (np.sum([self.max_left,self.max_right,self.cf_peak_load,self.cf_critical_load])>0):
              df_cf=pd.DataFrame([])
              df_cf['seconds']=self.cf_x
              df_cf['kg']=self.cf_y
              df_cf.to_csv( email + '_cf.csv' )
              
              df_mail = pd.DataFrame( self.source_results.data )
              df_mail.iloc[:,1::].to_csv( email + '_results.csv' )
                
                # print(text_input_mail.value)
        self.be1.on_click(save_data)
        
        # self.be2 = Button(label='Compare to previous tests')
        # def retrive_data():
        #     email = self.text_input_mail.value
        #     if len(email)>2 & ('@' in email):
        #         # save_data()
                
        #         resultfiles = glob.glob('*_results.csv')  
        #         if email + '_results.csv' in   resultfiles:                     
        #             df_results = pd.read_csv(  email + '_results.csv',index_col=0 )
        #             df_results['datetime'] = pd.to_datetime( df_results['datetime'] )         
        #             df_results=df_results.append( {'datetime':now,'max_left':self.max_left,'max_right':self.max_right,'peak_force':self.cf_peak_load,'critical_force':self.cf_critical_load,'rfd_left':self.rfd_left,'rfd_right':self.rfd_right},ignore_index=True )
        #             df_results=df_results.replace(0,np.nan)
        #             df_results=df_results.drop_duplicates()

        #             self.resultsource.data = df_results

        #         # print(text_input_mail.value)
        # self.be2.on_click(retrive_data)
        
        self.be3 = Button(label='Send results to e-mail')
        def sendmail():
          email = self.text_input_mail.value
          if len(email)>2 & ('@' in email) :
                        
                save_data()
                
                emailfrom = 'climbing.strength.test@gmail.com'
                emailto = email      
                password = 'ixaoacagxwdqsouy'  
                # ixaoacagxwdqsouy  climbing.strength.test@gmail.com
                msg = MIMEMultipart()
                msg["From"] = emailfrom
                msg["To"] = emailto
                msg["Subject"] = 'Climbing strength test results'
              
#                 msgtext ='''\
# Results:\n\
# Max. strength left hand: {:.2f} kg\n\
# Max. strength right hand: {:.2f} kg\n\
# Peak force: {:.2f} kg\n\
# Critical force: {:.2f} kg\n\
# Critical force: {:.2f} % of peak force\n\
# '''.format( self.max_left,self.max_right,self.cf_peak_load,self.cf_critical_load,self.cf_percent)
  
                msgtext = self.div_results.text              
                msg.attach(MIMEText( msgtext   ,'html'))
                
                att = email + '_results.csv'
                if os.path.exists( att ):
                    fp = open( att, "rb")
                    attachment = MIMEBase('application', 'x-csv')
                    attachment.set_payload(fp.read())
                    fp.close()
                    encoders.encode_base64(attachment)
                    attachment.add_header("Content-Disposition", "attachment", filename=att)
                    msg.attach(attachment)    
                att = email + '_cf.csv'
                if os.path.exists( att ):
                    fp = open( att, "rb")
                    attachment = MIMEBase('application', 'x-csv')
                    attachment.set_payload(fp.read())
                    fp.close()
                    encoders.encode_base64(attachment)
                    attachment.add_header("Content-Disposition", "attachment", filename=att)
                    msg.attach(attachment)  
                try:        
                    ctx = ssl.create_default_context()
                    server = smtplib.SMTP_SSL("smtp.gmail.com", port=465, context=ctx)
                    
                    server.login(emailfrom, password)
                    
                    # print(df_files_sent)
                
                    server.sendmail(emailfrom, emailto.split(','), msg.as_string())
                  
                    print('email sent: ' +   msg["Subject"] )
                    server.quit()

                except Exception as e:
                    print(e)
                                        
                    
        self.be3.on_click(sendmail)       
        
        self.text_input_bw = TextInput(value="", title="Enter body weight in kg to convert to %")

        
        self.be4 = Button(label="Back to main menue")
        def back():
                self.layout.children.pop()
                self.layout.children.pop()
                self.make_document_choice(doc)     
                doc.remove_periodic_callback(self.calback_update_mail)

        self.be4.on_click(back)
 
        widgets = column( self.text_input_mail,self.be1,self.be3,self.be4,self.text_input_bw,self.div_results ,width=400 ) 
        first_row = column(self.data_table,row(fig1,fig4,sizing_mode='stretch_both'),row(fig2,fig3,sizing_mode='stretch_both'),sizing_mode='stretch_both')
        
        self.layout=row(widgets, first_row,sizing_mode='stretch_height')
        doc.add_root(self.layout)
        
        doc.add_root(self.layout)
        
        self.calback_update_mail = doc.add_periodic_callback(self.update_email, 200)

    def update_email(self):    
          if self.cf_peak_load>0:          
              self.cf_percent=(self.cf_critical_load/self.cf_peak_load)*100
          

   
          email = self.text_input_mail.value
          if len(email)>2 & ('@' in email) :          
                self.be1.disabled = False
                # self.be2.disabled = False
                self.be3.disabled = False
                
                try:
                    resultfiles = glob.glob('*_results.csv')  
                    if email + '_results.csv' in   resultfiles:                     
                        df_old = pd.read_csv(  email + '_results.csv',index_col=0 )
                        df_old['datetime'] = pd.to_datetime( df_old['datetime'] ) 
                        df_new=pd.concat([self.df,df_old])
                        
                        # print(df_new)
                        
                        # self.df.loc[0 if pd.isnull(self.df.index.max()) else self.df.index.max() + 1]=[self.max_left,self.max_right,self.cf_peak_load,self.cf_critical_load,self.rfd_left,self.rfd_right]

                        # df_results=df_results.append( {'datetime':now,'max_left':self.max_left,'max_right':self.max_right,'peak_force':self.cf_peak_load,'critical_force':self.cf_critical_load,'rfd_left':self.rfd_left,'rfd_right':self.rfd_right},ignore_index=True )
                        df_new=df_new.replace(0,np.nan)
                        df_new=df_new.drop_duplicates()
    
                        self.source_results.data = df_new
                    else:
                        self.source_results.data = self.df

                except:
                    pass
                
          else:
                self.be1.disabled = True
                # self.be2.disabled = True
                self.be3.disabled = True
                self.source_results.data = self.df

                
                
          try:
              bw=float(self.text_input_bw.value)
              cf=self.cf_critical_load

              french_grades={1:'1',2:'2',3:'2+',4:'3-',5:'3',6:'3+',7:'4',8:'4+',9:'5',10:'5+',11:'6a',12:'6a+',13:'6b',14:'6b+',15:'6c',16:'6c+',17:'7a',18:'7a+',19:'7b',20:'7b+',21:'7c',22:'7c+',23:'8a',24:'8a+',25:'8b',26:'8b+',27:'8c',28:'8c+',29:'9a',30:'9a+'}
              
              prediction='<strong>Predicted redpoint grades (french sport):</strong><br><ul>'
              prediction+= '<li>If one predictor is far below the others, you might improve by focusing training here</li>'
              prediction+= '<li>If predictions are far below your real redpoint level, you might improve by focusing on techniqe and mental traning</li>'
              
              if self.max_right + self.max_left >0: 
                   maxxx=np.array( [self.max_right,self.max_left] )
                   max_onehand=np.mean( maxxx[maxxx>0] )
                   kg=max_onehand *2 -bw
                   if kg<=20:
                        gmin=7
                        gmax=11
                   else:    
                        irca = (kg*9.81 + 59.9 )/ 28.5 
                        gmin=np.round(irca)-2
                        gmax=np.round(irca)+2
                   if gmin < 1:
                       gmin=1
                   if gmax > 30:
                       gmax=30
                   if gmax < 1:
                       gmax=1
                   if gmin > 30:
                       gmin=30
                   prediction+= '<li>Max. strength: '+french_grades[gmin] +' - '+ french_grades[gmax]+'</li>'
                                              
              if cf>0:        
                  # irca = cf/bw* 100*0.3 + 6
                  gmin= np.round(cf/bw*100 *0.25 + 6 )
                  gmax= np.round(cf/bw*100 *0.35 + 6 )        
                  if gmin < 1:
                      gmin=1
                  if gmax > 30:
                      gmax=30
                  if gmax < 1:
                      gmax=1
                  if gmin > 30:
                      gmin=30
                  french_grades[gmin]
                  french_grades[gmax]
                  prediction+= '<li>Endurance: '+french_grades[gmin] +' - '+ french_grades[gmax]+'</li>'
    
    
              if  self.rfd_right+self.rfd_left>0 :       
                rfddd=np.array( [self.rfd_right,self.rfd_left] )
                rfd=np.mean( rfddd[rfddd>0] )
                # 117.8 irca - 798.3 = rfd new
                irca=(rfd*9.81 + 798.3) / 117.8
                gmin=np.round(irca)-1
                gmax=np.round(irca)+1       
                if gmin < 1:
                    gmin=1
                if gmax > 30:
                    gmax=30
                if gmax < 1:
                    gmax=1
                if gmin > 30:
                    gmin=30
                prediction+= '<li>Contact strength: '+french_grades[gmin] +' - '+ french_grades[gmax]+'</li>'
      
    
              self.div_results.text='<strong>Results:</strong> <br>\
    <ul>\
    <li>Max. strength left: {:.2f} % BW</li>\
    <li>Max. strength right: {:.2f} % BW</li>\
    <li>Peak force: {:.2f} % BW</li>\
    <li>Critical force: {:.2f} % BW</li>\
    <li>Critical force: {:.2f} % of peak force</li>\
    <li>RFD left: {:.2f} % kg/s</li>\
    <li>RFD right: {:.2f} % kg/s</li></ul>\
    '.format( (self.max_left/bw)*100,(self.max_right/bw)*100,(self.cf_peak_load/bw)*100,(self.cf_critical_load/bw)*100,self.cf_percent,self.rfd_left,self.rfd_right) 
     
              self.div_results.text+= prediction + '</ul>'            
   
    #           else:              
    #               self.div_results.text='<strong>Results:</strong> <br>\
    # <ul>\
    # <li>Max. strength left hand: {:.2f} % BW</li>\
    # <li>Max. strength right hand: {:.2f} % BW</li>\
    # <li>Peak force: {:.2f} % BW</li>\
    # <li>Critical force: {:.2f} % BW</li>\
    # <li>Critical force: {:.2f} % of peak force</li>\
    # <li>RFD left: {:.2f} % kg/s</li>\
    # <li>RFD right: {:.2f} % kg/s</li></ul>\
    # '.format( (self.max_left/bw)*100,(self.max_right/bw)*100,(self.cf_peak_load/bw)*100,(self.cf_critical_load/bw)*100,self.cf_percent,self.rfd_left,self.rfd_right) 
              
          except Exception as e:
            # print(e)  
            self.div_results.text='<strong>Results:</strong> <br>\
            <ul>\
            <li>Max. strength left hand: {:.2f} kg</li>\
            <li>Max. strength right hand: {:.2f} kg</li>\
            <li>Peak force: {:.2f} kg</li>\
            <li>Critical force: {:.2f} kg</li>\
            <li>Critical force: {:.2f} % of peak force</li>\
            <li>RFD left: {:.2f} % kg/s</li>\
            <li>RFD right: {:.2f} % kg/s</li>\
            </ul>'.format( self.max_left,self.max_right,self.cf_peak_load,self.cf_critical_load,self.cf_percent,self.rfd_left,self.rfd_right)               
              
        
        
    def check_for_timeout(self):
        self.seconds_left = (60*30) - (time.time() - self.timout_t0 )
        # print(self.seconds_left)
        if self.seconds_left < 0:
                self.layout.children.pop()
                self.layout.children.pop()
                self.make_login(self.doc)         
                self.doc.remove_periodic_callback(self.calback_timeout)


                
    def make_document_choice(self, doc):
        
        
        if self.tindeq is None:
            io_loop = tornado.ioloop.IOLoop.current()              
            io_loop.add_callback(connect, self)
        # if self.tindeq is not None:
        #     io_loop = tornado.ioloop.IOLoop.current()              
        #     io_loop.add_callback(tare, self)               


        # button_tare = Button(label="Tare")
        # def button_tarefunc():
        #         if self.tindeq is not None:
        #             io_loop = tornado.ioloop.IOLoop.current()              
        #             io_loop.add_callback(tare, self)               
        # button_tare.on_click(button_tarefunc)
        
        button_max = Button(label="Maximum strength test")
        def maxi():
                self.layout.children.pop()
                self.layout.children.pop()
                self.make_document_max(doc)         
        button_max.on_click(maxi)
        
        button_cft = Button(label="Endurance (Critical force) test")
        def cft():
                self.layout.children.pop()
                self.layout.children.pop()
                self.make_document_cft(doc)         
        button_cft.on_click(cft)
        
        button_send = Button(label="Show results & send mail")
        def sendmail():
                self.layout.children.pop()
                self.layout.children.pop()

                self.make_document_email(doc)         
        button_send.on_click(sendmail)

        button_live = Button(label="Live data")
        def livedata():
                self.layout.children.pop()
                self.layout.children.pop()
                self.make_document_live(doc)         
        button_live.on_click(livedata)

        button_train = Button(label="Training")
        def livedatatarget():
                self.layout.children.pop()
                self.layout.children.pop()
                self.make_document_livetarget(doc)         
        button_train.on_click(livedatatarget)


        button_rfd = Button(label="Rate of force development (Contact strength)")
        def butrfd():
                self.layout.children.pop()
                self.layout.children.pop()
                self.make_document_rfd(doc)         
        button_rfd.on_click(butrfd)
        
        button_quit = Button(label="Quit")
        def quitbut():
                self.layout.children.pop()
                self.layout.children.pop()
                self.make_login(doc)         
        button_quit.on_click(quitbut)

        div_timeleft = Div(text='Minutes left: '+str(int(self.seconds_left/60)),
                       style={'font-size': '100%', 'color': 'black',                             
                              'text-align': 'center'})              
        
        c = column(button_max,button_cft,button_rfd,button_send,button_live,button_train,button_quit)
        self.layout=column(c,column() )
        doc.add_root(self.layout)
        self.doc=doc

        
    def make_document_live(self, doc):
        self.reset()        

        self.source = ColumnDataSource(data=dict(x=[], y=[]))
        fig = figure(title='Real-time Data', sizing_mode='stretch_both', x_axis_label='Seconds', y_axis_label='kg')
        fig.line(x='x', y='y', source=self.source,line_width =2)
        doc.title = "Tindeq CFT"
        self.btn_go = Button(label='Waiting for Progressor...')
        self.btn_go.on_click(self.onclick_live)
        
        self.button_save = Button(label='Save and back to main menue')
        self.div_load = Div(text='Load: ---',
                       style={'font-size': '300%', 'color': 'black',                             
                              'text-align': 'center'})       
        
        def mainmenue():
                self.layout.children.pop()
                self.layout.children.pop()
                self.make_document_choice(doc)       
                doc.remove_periodic_callback(self.calback_update_live)
                if self.tindeq is not None:
                    io_loop = tornado.ioloop.IOLoop.current()              
                    io_loop.add_callback(stop_tindeq_logging, self)

        self.button_save.on_click(mainmenue)
 
        div_instruct = Div(text='Turn on tindeq device using small black button',\
                       style={'font-size': '100%', 'color': 'black',                             
                              'text-align': 'left'})        
        
        widgets = column( div_instruct,self.btn_go , self.button_save,self.div_load,width=400 ) 
        # first_row = row(widgets, fig)
        
        self.layout=row(widgets, fig)
        doc.add_root(self.layout)

        self.fig = fig
        self.calback_update_live = doc.add_periodic_callback(self.update_live, 50)
        self.btn_go.disabled=True


    def update_live(self):      
        
        if self.tindeq is not None:
                self.btn_go.disabled=False
                self.btn_go.label = 'Start data stream'

        self.source.stream({'x': self.xnew, 'y': self.ynew})       
        
        
        x=   np.array( self.source.data['x'] ,dtype=float ) 
        y=   np.array( self.source.data['y'] ,dtype=float ) 
        
        if len(x)>1:
        
            ix_valid = x > (x.max()-20)        
            self.source.data=dict(x=x[ix_valid], y= y[ix_valid])
            self.div_load.text = 'Load: '+str( np.abs(np.round(y[-1],2)) )  +' kg'
        self.reset()        

    def onclick_live(self):
        self.duration = 60*30
        self.reset()        
        self.source.data=dict(x=[], y=[])
        io_loop = tornado.ioloop.IOLoop.current()
        io_loop.add_callback(start_tindeq_logging, self)
###############

    def make_document_livetarget(self, doc):
        self.reset()        

        self.source = ColumnDataSource(data=dict(x=[], y=[]))
        self.source_end = ColumnDataSource(data=dict(x=[], y=[]))

        self.fig = figure(title='Real-time Data', sizing_mode='stretch_both', x_axis_label='Seconds', y_axis_label='kg')
        self.fig.line(x='x', y='y', source=self.source,line_width =2)
        self.fig.line(x='x', y='y', source=self.source_end,line_width =2,line_color='black',line_dash='dashed')
       
        self.btn_go = Button(label='Waiting for Progressor...')
        self.btn_go.on_click(self.onclick_livetarget)

        self.btn_stop = Button(label='Stop and reset')
        self.btn_stop.on_click(self.onclick_stop)
        
        self.button_save = Button(label='Back to main menue')
        self.div_load = Div(text='Load: ---',
                       style={'font-size': '300%', 'color': 'black',                             
                              'text-align': 'center'})       
        
        def mainmenue():
                self.layout.children.pop()
                self.layout.children.pop()
                self.make_document_choice(doc)       
                doc.remove_periodic_callback(self.calback_update_livetarget)
                if self.tindeq is not None:
                    io_loop = tornado.ioloop.IOLoop.current()              
                    io_loop.add_callback(stop_tindeq_logging, self)

        self.button_save.on_click(mainmenue)
 
        div_instruct = Div(text='Turn on tindeq device using small black button',\
                       style={'font-size': '100%', 'color': 'black',                             
                              'text-align': 'left'})  
            
        self.spinner_on = Spinner(title="Pull time in s", low=1, step=1, value=10)
        self.spinner_rest = Spinner(title="Rest time in s", low=1, step=1, value=6)
        self.spinner_force = Spinner(title="Target force in kg", low=1, step=1, value=50)
        self.spinner_reps = Spinner(title="Repetitions", low=1, step=1, value=10)
        r1=row(self.spinner_on,self.spinner_rest,sizing_mode='scale_width')
        r2=row(self.spinner_force,self.spinner_reps,sizing_mode='scale_width')
        
        # s=5
        # dur =  self.spinner_on.value +  self.spinner_rest.value
        # r=np.arange(self.spinner_reps.value)
        # self.target_boxes= self.fig.quad(top=self.spinner_force.value+5, bottom=self.spinner_force.value-5, left=s+r*dur,
        #            right=s+r*dur +self.spinner_on.value, color='red',alpha=0.5)        
        self.source_targetbox= ColumnDataSource(data=dict(t=[], b=[], l=[], r=[]))
        self.fig.quad(top='t', bottom='b', left='l', right='r', source=self.source_targetbox, color='red',alpha=0.5)        
             
        
        widgets = column( div_instruct,r1,r2,self.btn_go ,  self.btn_stop,self.button_save,self.div_load,width=400 ) 
        # first_row = row(widgets, fig)
        
        self.layout=row(widgets, self.fig)
        doc.add_root(self.layout)

        # self.fig = fig
        self.calback_update_livetarget = doc.add_periodic_callback(self.update_livetarget, 50)
        self.btn_go.disabled=True

    def update_livetarget(self):      
        
        if self.tindeq is not None:
                self.btn_go.disabled=False
                self.btn_go.label = 'Start data stream'

        self.source.stream({'x': self.xnew, 'y': self.ynew})       


        # self.fig.y_range.start=0           
        # self.fig.y_range.end=self.spinner_force.value+10   
        
        # print(   self.source_targetbox.data)
     
        
        # for r in range(self.spinner_reps.value):
        #     dur =  self.spinner_on.value +  self.spinner_rest.value
        #     self.fig.quad(top=self.spinner_force.value+5, bottom=self.spinner_force.value-5, left=s+r*dur,
        #            right=s+r*dur +self.spinner_on.value, color='red',alpha=0.5)        
        
        x=   np.array( self.source.data['x'] ,dtype=float ) 
        y=   np.array( self.source.data['y'] ,dtype=float ) 
                     
        s=5
        dur =  self.spinner_on.value +  self.spinner_rest.value
        r=np.arange(self.spinner_reps.value)      
        tt= self.spinner_force.value+2 *np.ones(len(r)) 
        bb=self.spinner_force.value-2 *np.ones(len(r))  
        ll=s+r*dur
        rr= s+r*dur+self.spinner_on.value
        self.source_targetbox.data= dict(t=tt, b=bb, l=ll, r=rr)
           
        if len(x)>1:   
            self.source_end.data={'x': [np.max(x),np.max(x)], 'y': [0,self.spinner_force.value+1]}       

            # ix_valid = x > (x.max()-30)        
            # self.source.data=dict(x=x, y= y)
            self.div_load.text = 'Load: '+str( np.abs(np.round(y[-1],2)) )  +' kg'
            # t=x[ix_valid]
            # t[-1]=t[-1]+5
            
            # ix_box = ((rr>t[0]) & (ll<t[0]) ) | ( (ll<t[-1]) & (rr>t[-1])) | ( (ll>=t[0]) & (rr<=t[-1]) )
            
            # tt2=tt[ix_box]
            # bb2=bb[ix_box]
            # ll2=ll[ix_box]
            # rr2=rr[ix_box]

            # ll2[ll2<t[0]]=t[0]
            # rr2[rr2>t[-1]]=t[-1]         
                        
            # self.source_targetbox.data= dict(t=tt2, b=bb2, l=ll2, r=rr2)
            
            # self.fig.x_range.start=t[0]            
            # self.fig.x_range.end=t[-1]    
            
                  
        self.reset()    
        

    def onclick_stop(self):
        io_loop = tornado.ioloop.IOLoop.current()
        io_loop.add_callback(stop_tindeq_logging, self)
        self.reset()        
        self.source.data=dict(x=[], y=[])
        self.source_end.data=dict(x=[], y=[])     

        
    def onclick_livetarget(self):
        self.reset()        
        self.source.data=dict(x=[], y=[])
        self.source_end.data=dict(x=[], y=[])     

        io_loop = tornado.ioloop.IOLoop.current()
        io_loop.add_callback(start_tindeq_logging, self)
        
        # s=1
        # dur =  self.spinner_on.value +  self.spinner_rest.value
        # r=np.arange(self.spinner_reps.value)      
        # tt= self.spinner_force.value+5 *np.ones(len(r)) 
        # bb=self.spinner_force.value-5 *np.ones(len(r))  
        # ll=s+r*dur
        # rr= s+r*dur+self.spinner_on.value
        # self.source_targetbox.data= dict(t=tt, b=bb, l=ll, r=rr)       

########        
    def make_document_max(self, doc):
        self.reset()        

        self.source = ColumnDataSource(data=dict(x=[], y=[]))
        fig = figure(title='Real-time Data', sizing_mode='stretch_both', x_axis_label='Seconds', y_axis_label='kg')
        fig.line(x='x', y='y', source=self.source,line_width =2)
        doc.title = "Tindeq CFT"
        self.btn_left = Button(label='Waiting for Progressor...')
        self.btn_right = Button(label='Waiting for Progressor...')
        # button_reset = Button(label='Reset')

        
        div_instruct = Div(text='<strong>Instructions:</strong> <br>\
                                <ul>\
                                  <li>Turn on tindeq device (small black button)</li>\
                                  <li>Pull as hard as you can on 20mm edge!</li>\
                                  <li>Increase force until you reach your maximum, than stop</li>\
                                  <li>Each tests runs for 20s</li>\
                                </ul>',
                       style={'font-size': '100%', 'color': 'black',                             
                              'text-align': 'left'})
        
        
        self.div_lh = Div(text='Left hand: ---',
                       style={'font-size': '200%', 'color': 'black',                             
                              'text-align': 'center'})
        self.div_rh = Div(text='Right hand: ---',
                       style={'font-size': '200%', 'color': 'black',                             
                              'text-align': 'center'})
        

        self.btn_left.on_click(self.onclick_left)
        self.btn_right.on_click(self.onclick_right)
        
        self.button_save = Button(label='Save and back to main menue')
        def mainmenue():
                self.layout.children.pop()
                self.layout.children.pop()
                self.make_document_choice(doc)       
                doc.remove_periodic_callback(self.calback_update_max)
                if self.tindeq is not None:
                    io_loop = tornado.ioloop.IOLoop.current()              
                    io_loop.add_callback(stop_tindeq_logging, self)
        self.button_save.on_click(mainmenue)
        
        
        widgets = column( div_instruct,self.btn_left ,self.div_lh,self.btn_right,self.div_rh, self.button_save,width=400 ) 
        # first_row = row(widgets, fig)
        
        self.layout=row(widgets, fig)
        doc.add_root(self.layout)


        self.fig = fig
        self.calback_update_max = doc.add_periodic_callback(self.update_max, 50)

        self.btn_right.disabled=True
        self.btn_left.disabled=True
        # self.button_save.disabled=True        

    def onclick_left(self):
        self.duration = 20
        self.source.data=dict(x=[], y=[])
        self.maxtest_left=True
        self.maxtest_right=False
        def sctn():  
            self.maxtest_left=False 
        s = threading.Timer(self.duration, sctn)  
        s.start()  
        io_loop = tornado.ioloop.IOLoop.current()
        io_loop.add_callback(start_test_max, self)

    def onclick_right(self):
        self.duration = 20
        self.source.data=dict(x=[], y=[])
        self.maxtest_right=True
        self.maxtest_left=False
        # self.btn_right.disabled=True
        # self.btn_left.disabled=True

        def sctn():  
            self.maxtest_right=False 
        s = threading.Timer(self.duration, sctn  )
        s.start()  
        io_loop = tornado.ioloop.IOLoop.current()
        io_loop.add_callback(start_test_max, self)
    
        
    def update_max(self):    
        
            self.source.stream({'x': self.xnew, 'y': self.ynew})
            
            if (len( self.source.data['y'] )>1) & (self.maxtest_right):
                self.max_right= np.round( np.max( np.array( self.source.data['y'] ,dtype=float ) ),2)
                self.btn_right.disabled=True
                self.btn_left.disabled=True
                self.button_save.disabled=True

            self.div_rh.text = 'Right hand: '+str( self.max_right )  +' kg'

            if (len( self.source.data['y'] )>1) & (self.maxtest_left):
                self.max_left= np.round( np.max( np.array( self.source.data['y'] ,dtype=float ) ),2)
                self.btn_right.disabled=True
                self.btn_left.disabled=True
                self.button_save.disabled=True
                
            if (self.maxtest_right==False) & (self.maxtest_left==False) & (self.tindeq is not None):      
                self.btn_right.disabled=False
                self.btn_left.disabled=False
                self.button_save.disabled=False
                self.btn_right.label = 'Start right hand test'
                self.btn_left.label = 'Start left hand test'
        
            self.div_lh.text = 'Left hand: '+str( self.max_left )  +' kg'

               
            
            # nlaps = self.duration // 10
            # self.laps.text = f"Rep {1 + nlaps - self.reps}/{nlaps}"
            self.reset()
            
    def make_document_cft(self, doc):
        
        self.x = []
        self.y = []
        # self.xnew = []
        # self.ynew = []
        self.active = False
        self.duration = 240
        self.reps = 25
        self.state = IdleState
        self.test_done = False
        self.analysed = False
        
   
        
        source = ColumnDataSource(data=dict(x=[], y=[]))
        fig = figure(title='Real-time Data', sizing_mode='stretch_both', x_axis_label='Seconds', y_axis_label='kg')
        fig.line(x='x', y='y', source=source,line_width =2)
        doc.title = "Tindeq CFT"
        self.btn = Button(label='Waiting for Progressor...')
        button_save = Button(label='Save and back to main menue')
        def mainmenue():
                self.layout.children.pop()
                self.layout.children.pop()
                self.make_document_choice(doc)       
                self.state= IdleState
                self.active=False 
                doc.remove_periodic_callback(self.calback_update_cft)
                if self.tindeq is not None:
                    io_loop = tornado.ioloop.IOLoop.current()              
                    io_loop.add_callback(stop_tindeq_logging, self)
                # await self.tindeq.stop_logging_weight()       
                
        button_save.on_click(mainmenue)        
        
        div_instruct = Div(text='<strong>Instructions:</strong> <br>\
                                <ul>\
                                  <li>Turn on tindeq device (small black button)</li>\
                                  <li>Use only left or right hand</li>\
                                  <li>Test starts with 10s countdown</li>\
                                  <li>Than pull has hard as you can on 20mm edge for 7s</li>\
                                  <li>Short 3s rest</li>\
                                  <li>Repeat 25x and get ridiculously pumped</li>\
                                </ul>',
                       style={'font-size': '100%', 'color': 'black',                             
                              'text-align': 'left'})
                
        self.duration_slider = Slider(start=5, end=30, value=25,
                                 step=1, title="Reps")
        self.laps = Div(text=f'Rep {0}/{self.duration_slider.value}',
                        style={'font-size': '400%', 'color': 'black',
                               'text-align': 'center'})
        self.div = Div(text='10:00',
                       style={'font-size': '800%', 'color': 'white',
                              'background-color': 'orange',
                              'text-align': 'center'})
        self.results_div = Div(text='', sizing_mode='stretch_width',
                               style={'font-size': '150%', 'color': 'black',
                                      'text-align': 'left'})

        def onclick():
            self.reps = self.duration_slider.value
            self.duration = self.reps * 10 +10
            io_loop = tornado.ioloop.IOLoop.current()
            io_loop.add_callback(start_test_cft, self)
            self.reset()        
            self.source.data=dict(x=[], y=[])
            
            io_loop.add_callback(start_tindeq_logging, self)            

        self.btn.on_click(onclick)
        self.btn.disabled=True
        
        widgets = column(div_instruct,self.duration_slider, self.btn,button_save, self.laps, self.div,self.results_div)
        self.layout = row(widgets, fig)
        doc.add_root(self.layout)
        self.source = source
        self.fig = fig
        self.calback_update_cft = doc.add_periodic_callback(self.update_cft, 50)
        

    def analyse_cft(self):
            x = np.array(self.x)
            y = np.array(self.y)        
            
            nlaps = (self.duration // 10) -1

            # ix_lap= np.zeros(len(x))
            
            tmeans=[]
            fmeans=[]
            std_fmeans=[]
            
            for n in range(nlaps):
                t1 = 10+n*10
                t2=10+n*10+7             
                ix = (x>=t1) & (x<=t2) & (y>3)
                # ix_lap[ix]=n+1
                
                tmeans.append( np.mean(x[ix]) ) 
                fmeans.append( np.median(y[ix]) ) 
                iqr = np.percentile(y[ix],75) - np.percentile(y[ix],25)
                std_fmeans.append( iqr/2 )                             
                # print([t1,t2])
            
            tmeans=np.array(tmeans)
            fmeans=np.array(fmeans)
            std_fmeans=np.array(std_fmeans)
            # breakpoint()
            
            self.cf_peak_load = np.max(fmeans)
            imax=np.argmax(fmeans)
            
            self.cf_critical_load = np.nanmean(fmeans[-5:-1])
            std_load_asymptote = np.nanstd(fmeans[-5:-1])
            self.cf_x = x  
            self.cf_y = y  
            
            msg= '<p>Peak force = {:.2f} +/- {:.2f} kg</p>'.format( fmeans[imax], std_fmeans[imax])
            msg += '<p>Critical force = {:.2f} +/- {:.2f} kg</p>'.format(self.cf_critical_load, std_load_asymptote) 
            msg += '<p>Critical force = {:.2f} % of peak force</p>'.format(100*self.cf_critical_load/fmeans[imax]) 
            self.results_div.text = msg        

            self.fig.circle(tmeans, fmeans, color='red', size=20, line_alpha=0)
            

            # esource = ColumnDataSource(dict(x=tmeans, upper=fmeans+std_fmeans, lower=fmeans-std_fmeans))
            # self.fig.add_layout(Whisker(source=esource, base='x', upper='upper', lower='lower', level='overlay'))    

    def update_cft(self):
        if self.test_done and not self.analysed:
            # self.btn.label = 'Restart test'
            # np.savetxt('critical_force_test.txt', np.column_stack((self.x, self.y)))
            # try:
            #       export_png(self.fig, filename="critical_force_test.png")
            # except Exception as e  :
            #       print(e)        
            try:
                self.analyse_cft()                         
            except Exception as e  :
                 print(e)
            self.analysed = True
        else:
            if (self.tindeq is not None) & (self.active==False):
                self.btn.disabled=False
                self.btn.label = 'Start Test'
            if self.active==True:
                self.btn.disabled=True

            self.state.update_cft(self)
            self.source.stream({'x': self.xnew, 'y': self.ynew})
            nlaps = self.duration_slider.value
            if self.active==False:
                self.laps.text = f"Rep 0/{nlaps}"
            else:
                self.laps.text = f"Rep { 1 + nlaps - self.reps}/{nlaps}"
            self.reset()
##########

    def make_document_rfd(self, doc):
        self.reset()        

        self.source = ColumnDataSource(data=dict(x=[], y=[]))
        fig = figure(title='Real-time Data', sizing_mode='stretch_both', x_axis_label='Seconds', y_axis_label='kg')
        fig.line(x='x', y='y', source=self.source,line_width =2)
        
        self.source_rfd = ColumnDataSource(data=dict(x=[], y=[]))
        fig.line(x='a', y='b', source=self.source_rfd,line_width =2,color='red')

        doc.title = "Tindeq CFT"
        self.btn_left = Button(label='Waiting for Progressor...')
        self.btn_right = Button(label='Waiting for Progressor...')
        # button_reset = Button(label='Reset')

        
        div_instruct = Div(text='<strong>Instructions:</strong> <br>\
                                <ul>\
                                  <li>Turn on tindeq device (small black button)</li>\
                                  <li>Pull as fast as you can on 20mm edge!</li>\
                                  <li>Each tests runs for 10s</li>\
                                </ul>',
                       style={'font-size': '100%', 'color': 'black',                             
                              'text-align': 'left'})
        
        
        self.div_lh = Div(text='RFD Left hand: ---',
                       style={'font-size': '150%', 'color': 'black',                             
                              'text-align': 'center'})
        self.div_rh = Div(text='RFD Right hand: ---',
                       style={'font-size': '150%', 'color': 'black',                             
                              'text-align': 'center'})
        

        self.btn_left.on_click(self.onclick_left_rdf)
        self.btn_right.on_click(self.onclick_right_rdf)
        
        self.button_save = Button(label='Save and back to main menue')
        def mainmenue():
                self.layout.children.pop()
                self.layout.children.pop()
                self.make_document_choice(doc)       
                doc.remove_periodic_callback(self.calback_update_max)
                if self.tindeq is not None:
                    io_loop = tornado.ioloop.IOLoop.current()              
                    io_loop.add_callback(stop_tindeq_logging, self)
        self.button_save.on_click(mainmenue)
        
        
        widgets = column( div_instruct,self.btn_left ,self.div_lh,self.btn_right,self.div_rh, self.button_save,width=400 ) 
        # first_row = row(widgets, fig)
        
        self.layout=row(widgets, fig)
        doc.add_root(self.layout)


        self.fig = fig

        self.calback_update_max = doc.add_periodic_callback(self.update_rfd, 50)

        self.btn_right.disabled=True
        self.btn_left.disabled=True
        # self.button_save.disabled=True        
        self.rfd_right_done=False
        self.rfd_left_done=False

    def onclick_left_rdf(self):
        self.duration = 10
        self.source.data=dict(x=[], y=[])
        self.maxtest_left=True
        self.maxtest_right=False
        def sctn():  
            self.maxtest_left=False 
            self.rfd_left_done=True
        s = threading.Timer(self.duration, sctn)  
        s.start()  
        io_loop = tornado.ioloop.IOLoop.current()
        io_loop.add_callback(start_test_max, self)

    def onclick_right_rdf(self):
        self.duration = 10
        self.source.data=dict(x=[], y=[])
        self.maxtest_right=True
        self.maxtest_left=False
        # self.btn_right.disabled=True
        # self.btn_left.disabled=True

        def sctn():  
            self.maxtest_right=False 
            self.rfd_right_done=True

        s = threading.Timer(self.duration, sctn  )
        s.start()  
        io_loop = tornado.ioloop.IOLoop.current()
        io_loop.add_callback(start_test_max, self)


    def update_rfd(self):    
        
            self.source.stream({'x': self.xnew, 'y': self.ynew})
            
            if (len( self.source.data['y'] )>1) & (self.maxtest_right):
                # self.max_right= np.round( np.max( np.array( self.source.data['y'] ,dtype=float ) ),2)
                self.btn_right.disabled=True
                self.btn_left.disabled=True
                # self.source_rfd = ColumnDataSource(data=dict(x=[], y=[]))

            #     self.button_save.disabled=True


            if (len( self.source.data['y'] )>1) & (self.maxtest_left):
                # self.max_left= np.round( np.max( np.array( self.source.data['y'] ,dtype=float ) ),2)
                self.btn_right.disabled=True
                self.btn_left.disabled=True
                # self.source_rfd = ColumnDataSource(data=dict(x=[], y=[]))

            #     self.button_save.disabled=True
                
            if (self.maxtest_right==False) & (self.maxtest_left==False) & (self.tindeq is not None):      
                self.btn_right.disabled=False
                self.btn_left.disabled=False
                self.button_save.disabled=False
                self.btn_right.label = 'Start right hand test'
                self.btn_left.label = 'Start left hand test'
                
            if self.rfd_left_done & (self.maxtest_right==False):
                x=np.array( self.source.data['x'])
                y=np.array(self.source.data['y'])
                            
                ymax=np.max(y)
                f80=(ymax*0.8)
                f20=(ymax*0.2)

                ix= np.where( y>f80 )[0]                
                t80 = x[ix[0]]
                ix= np.where( y>f20)[0]                
                t20 = x[ix[0]]  
                f=(f80-f20)
                t= t80-t20
                
                self.rfd_left= np.round(f/t,2)
                self.div_lh.text = 'RFD (20%-80%) Left hand: '+str( self.rfd_left )  +' kg/s'               
                self.source_rfd.data=dict(a=[t20,t80],b=[f20,f80])
                self.rfd_left_done=False

            if self.rfd_right_done & (self.maxtest_left==False):
                x=np.array( self.source.data['x'])
                y=np.array(self.source.data['y'])
                            
                ymax=np.max(y)
                f80=(ymax*0.8)
                f20=(ymax*0.2)

                ix= np.where( y>f80 )[0]                
                t80 = x[ix[0]]
                ix= np.where( y>f20)[0]                
                t20 = x[ix[0]]  
                f=(f80-f20)
                t= t80-t20
                
                self.rfd_right= np.round(f/t,2)
                self.div_rh.text = 'RFD (20%-80%) Right hand: '+str( self.rfd_right )  +' kg/s'               
                self.source_rfd.data=dict(a=[t20,t80],b=[f20,f80])
                self.rfd_right_done=False
               
            
            # nlaps = self.duration // 10
            # self.laps.text = f"Rep {1 + nlaps - self.reps}/{nlaps}"
            self.reset()
            
            
###################################
async def connect(cft):
    tindeq = TindeqProgressor(cft)
    await tindeq.connect()
    cft.tindeq = tindeq
    await cft.tindeq.tare()
    print('TARE')
    # await cft.tindeq.soft_tare()
    await asyncio.sleep(2)


async def start_test_max(cft):
    try:

        # cft.state.end(cft)
        await cft.tindeq.start_logging_weight()
        # await asyncio.sleep(cft.state.duration)

        print('Test starts!')
        # cft.state.end(cft)
        cft.active = True
        await asyncio.sleep(cft.duration)
        await cft.tindeq.stop_logging_weight()
        cft.test_done = True
        await asyncio.sleep(0.5)
        # cft.state = IdleState
    except Exception as err:
        print(str(err))
    # finally:
        # await cft.tindeq.disconnect()
        # cft.tindeq = None
        
async def start_test_cft(cft):
    try:
        # cft.state.end(cft)

        # cft.state.end(cft)
        # await cft.tindeq.start_logging_weight()
        # await asyncio.sleep(cft.state.duration)

        print('Test starts!')
        cft.state.end(cft)
        cft.active = True
        await asyncio.sleep(cft.duration-3)
        cft.test_done = True
        cft.state = IdleState
        await asyncio.sleep(1)
        await cft.tindeq.stop_logging_weight()
        cft.active = False

    except Exception as err:
        print(str(err))
    # finally:
    #     await cft.tindeq.disconnect()
    #     cft.tindeq = None
    
async def tare(cft):
    try:
        await cft.tindeq.tare()
        print('TARE')
    except Exception as err:
        print(str(err))
    

async def start_tindeq_logging(cft):
    try:
        await cft.tindeq.start_logging_weight()
        print('Logging starts!')
        cft.active = True       
    except Exception as err:
        print(str(err))

async def stop_tindeq_logging(cft):
    try:
        await cft.tindeq.stop_logging_weight()
        # await asyncio.sleep(0.5)
        print('Logging stops!')
        cft.active = False       
    except Exception as err:
        print(str(err))
        
cft = CFT()
cft.make_gui(curdoc())

apps = {'/': Application(FunctionHandler(cft.make_gui))}
server = Server(apps, port=5000 )
server.start()

if __name__ == "__main__":
    tornado.platform.asyncio.AsyncIOMainLoop().install()
    io_loop = tornado.ioloop.IOLoop.current()
    print('Opening Bokeh application on http://localhost:5006/')
    io_loop.add_callback(server.show, "/")
    io_loop.start()
