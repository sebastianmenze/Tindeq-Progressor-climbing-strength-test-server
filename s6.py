from src.tindeq import TindeqProgressor
from src.analysis import analyse_data


import time

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
from bokeh.models import Button, Slider, Div, Band, Whisker

from bokeh.models import Button, CustomJS, PasswordInput, PreText, TextInput

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
            st.start('countdown.mp3',3.5)   
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
        if (remain<=1.5) & (remain>.5) & (st.running==False ):   
            st.start('end.wav',1.2)  
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
            st.start('countdown.mp3',3.5)   
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
        io_loop = tornado.ioloop.IOLoop.current()
        # io_loop.add_callback(connect, self)
        self.pwd = 'pw'
        
        self.maxtest_right=False 
        self.maxtest_left=False 
        self.max_right=0 
        self.max_left=0 
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
        
        password = PasswordInput(title="Password:")
        button = Button(label="Get started!")

        # secret = PreText() # Secret information displayed if correct password entered
        # # Verify if the password typed is bokeh using a JS script
        # verify = CustomJS(args=dict(password=password, secret=secret), code="""
        #     secret.text = 'Wrong Password.';
        #     if (password.value == %r ) {
        #         secret.text = 'Correct Password. The Secret is 42.';
        #     }
        # """ % (PASSWD))      
        # password.js_on_change('value', verify)
        # button.js_on_event('button_click', verify)
        
        
        # secret = PreText() # Secret information displayed if correct password entered
        # Verify if the password typed is bokeh using a JS script
        def verify():
            if password.value==self.pwd:
                self.layout.children.pop()
                self.layout.children.pop()
                self.make_document_choice(doc)              
        
        button.on_click(verify)
    
        self.layout=column(password,button)
        doc.add_root(self.layout)

    def make_gui(self,doc):
        self.make_login(doc)
        
    def make_document_email(self, doc):
        
        now = pd.to_datetime("today").date()
        
        div_results = Div(text='<strong>Results:</strong> <br>\
                                <ul>\
                                  <li>Max. strength left hand: {:.2f} kg</li>\
                                  <li>Max. strength right hand: {:.2f} kg</li>\
                                  <li>Peak force: {:.2f} kg</li>\
                                  <li>Critical force: {:.2f} kg</li>\
                                </ul>'.format( self.max_left,self.max_right,self.cf_peak_load,self.cf_critical_load) ,
                       style={'font-size': '150%', 'color': 'black',                             
                              'text-align': 'left'})


        # self.resultsource = ColumnDataSource(data=dict(x=self.cf_x, y=self.cf_y))
        # fig = figure( sizing_mode='stretch_both', x_axis_label='Seconds', y_axis_label='kg')
        # fig.line(x='x', y='y', source=self.resultsource)
        self.resultsource = ColumnDataSource(data=dict([]))
        fig1 = figure( title='Max. Strength',sizing_mode='stretch_both', y_axis_label='kg',x_axis_type='datetime')
        fig1.line(x='datetime', y='max_left', source=self.resultsource,color='red',legend_label="left")
        fig1.circle(x='datetime', y='max_left', source=self.resultsource,color='red')
        fig1.line(x='datetime', y='max_right', source=self.resultsource,color='blue',legend_label="right")
        fig1.circle(x='datetime', y='max_right', source=self.resultsource,color='blue')
        fig1.legend.location = "top_left"

        fig2 = figure( title='Peak force',sizing_mode='stretch_both', y_axis_label='kg',x_axis_type='datetime')
        fig2.line(x='datetime', y='peak_force', source=self.resultsource,color='red')
        fig2.circle(x='datetime', y='peak_force', source=self.resultsource,color='red')

        fig3 = figure( title='Critical force',sizing_mode='stretch_both', y_axis_label='kg',x_axis_type='datetime')
        fig3.line(x='datetime', y='critical_force', source=self.resultsource,color='red')
        fig3.circle(x='datetime', y='critical_force', source=self.resultsource,color='red')        
                
            
        text_input_mail = TextInput(value="", title="E-mail:")

        self.be1 = Button(label='Save results to database')
        def save_data():
            email = text_input_mail.value
            if len(email)>2 & ('@' in email) & (np.sum([self.max_left,self.max_right,self.cf_peak_load,self.cf_critical_load])>0):
              df_cf=pd.DataFrame([])
              df_cf['seconds']=self.cf_x
              df_cf['kg']=self.cf_y
              df_cf.to_csv( email + '_cf.csv' )
                
              resultfiles = glob.glob('*_results.csv')  
              if email + '_results.csv' in   resultfiles:
                df_results = pd.read_csv(  email + '_results.csv',index_col=0 )
              else:                   
                df_results=pd.DataFrame(columns=['datetime','max_left','max_right','peak_force','critical_force'])
              df_results=df_results.append( {'datetime':now,'max_left':self.max_left,'max_right':self.max_right,'peak_force':self.cf_peak_load,'critical_force':self.cf_critical_load},ignore_index=True )
              df_results=df_results.drop_duplicates()
              df_results.to_csv( email + '_results.csv' )
                
                # print(text_input_mail.value)
        self.be1.on_click(save_data)
        
        self.be2 = Button(label='Compare to previous tests')
        def retrive_data():
            email = text_input_mail.value
            if len(email)>2 & ('@' in email):
                # save_data()
                
                resultfiles = glob.glob('*_results.csv')  
                if email + '_results.csv' in   resultfiles:                     
                    df_results = pd.read_csv(  email + '_results.csv',index_col=0 )
                    df_results['datetime'] = pd.to_datetime( df_results['datetime'] )         
                    df_results=df_results.append( {'datetime':now,'max_left':self.max_left,'max_right':self.max_right,'peak_force':self.cf_peak_load,'critical_force':self.cf_critical_load},ignore_index=True )
                    df_results=df_results.drop_duplicates()

                    self.resultsource.data = df_results

                # print(text_input_mail.value)
        self.be2.on_click(retrive_data)
        
        self.be3 = Button(label='Send results to e-mail')
        def sendmail():
          email = text_input_mail.value
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
              
                msgtext ='''
                Results:\n\
                Max. strength left hand: {:.2f} kg\n\
                Max. strength right hand: {:.2f} kg\n\
                Peak force: {:.2f} kg\n\
                Critical force: {:.2f} kg\n\
                '''.format( self.max_left,self.max_right,self.cf_peak_load,self.cf_critical_load)
                
                msg.attach(MIMEText( msgtext   ,'plain'))
                
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

        self.be4 = Button(label="Back to main menue")
        def back():
                self.layout.children.pop()
                self.layout.children.pop()
                self.make_document_choice(doc)     
                doc.remove_periodic_callback(self.calback_update_mail)

        self.be4.on_click(back)
 
        self.text_input_mail=text_input_mail
        widgets = column( div_results,text_input_mail,self.be1,self.be2,self.be3,self.be4 ,width=400 ) 
        first_row = row(fig1,fig2,fig3)
        
        self.layout=row(widgets, first_row)
        doc.add_root(self.layout)
        
        doc.add_root(self.layout)
        
        self.calback_update_mail = doc.add_periodic_callback(self.update_email, 50)

    def update_email(self):    
          email = self.text_input_mail.value
          if len(email)>2 & ('@' in email) :          
                self.be1.disabled = False
                self.be2.disabled = False
                self.be3.disabled = False
          else:
                self.be1.disabled = True
                self.be2.disabled = True
                self.be3.disabled = True
        
    def check_for_timeout(self):
        elapsed = time.time() - self.timout_t0 
        # print(elapsed)
        if elapsed > (60*30):
                self.layout.children.pop()
                self.layout.children.pop()
                self.make_login(self.doc)         
                self.doc.remove_periodic_callback(self.calback_timeout)


                
    def make_document_choice(self, doc):
        
        self.timout_t0=  time.time()
        
        if self.tindeq is None:
            io_loop.add_callback(connect, self)

        
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

        button_quit = Button(label="Quit")
        def quitbut():
                self.layout.children.pop()
                self.layout.children.pop()
                self.make_login(doc)         
        button_quit.on_click(quitbut)
        
        c = column(button_max,button_cft,button_send,button_quit)
        self.layout=column(c,column() )
        doc.add_root(self.layout)
        self.doc=doc
        self.calback_timeout = doc.add_periodic_callback(self.check_for_timeout, 100)
        
    def make_document_max(self, doc):
        source = ColumnDataSource(data=dict(x=[], y=[]))
        fig = figure(title='Real-time Data', sizing_mode='stretch_both', x_axis_label='Seconds', y_axis_label='kg')
        fig.line(x='x', y='y', source=source)
        doc.title = "Tindeq CFT"
        self.btn_left = Button(label='Start left hand test')
        self.btn_right = Button(label='Start right hand test')
        # button_reset = Button(label='Reset')

        
        div_instruct = Div(text='<strong>Instructions:</strong> <br>\
                                <ul>\
                                  <li>Turn on tindeq device (small black button)</li>\
                                  <li>Pull as hard as you can on 20mm edge!</li>\
                                  <li>Increase force slowly until you reach your maximum</li>\
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
        
        # self.div = Div(text='0 kg',
        #                style={'font-size': '600%', 'color': 'red',                             
        #                       'text-align': 'center'})
        # self.results_div = Div(text='', sizing_mode='stretch_width',
        #                        style={'font-size': '150%', 'color': 'black',
        #                               'text-align': 'left'})
        # def reset():
        #     self.source.data=dict(x=[], y=[])
        #     self.div.text = '0 kg'
        # button_reset.on_click(reset)
        
        # def onclick_left(self):
        #     self.duration = 30
        #     self.source.data=dict(x=[], y=[])
        #     self.maxtest_left=True
        #     def sctn():  
        #         self.maxtest_left=False 
        #     s = threading.Timer(self.duration, sctn)  
        #     s.start()  
        #     io_loop = tornado.ioloop.IOLoop.current()
        #     io_loop.add_callback(start_test_max, self)
        self.btn_left.on_click(self.onclick_left)

        # def onclick_right(self):
        #     self.duration = 30
        #     self.source.data=dict(x=[], y=[])
        #     self.maxtest_right=True
        #     def sctn():  
        #         self.maxtest_right=False 
        #     s = threading.Timer(self.duration, sctn)  
        #     s.start()  
        #     io_loop = tornado.ioloop.IOLoop.current()
        #     io_loop.add_callback(start_test_max, self)
        self.btn_right.on_click(self.onclick_right)
        
        self.button_save = Button(label='Save and back to main menue')
        def mainmenue():
                self.layout.children.pop()
                self.layout.children.pop()
                self.make_document_choice(doc)       
                doc.remove_periodic_callback(self.calback_update_max)

        self.button_save.on_click(mainmenue)
        
        
        widgets = column( div_instruct,self.btn_left ,self.div_lh,self.btn_right,self.div_rh, self.button_save,width=400 ) 
        # first_row = row(widgets, fig)
        
        self.layout=row(widgets, fig)
        doc.add_root(self.layout)


        self.source = source
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
        self.reps = 24
        self.state = IdleState
        self.test_done = False
        self.analysed = False
        
   
        
        source = ColumnDataSource(data=dict(x=[], y=[]))
        fig = figure(title='Real-time Data', sizing_mode='stretch_both', x_axis_label='Seconds', y_axis_label='kg')
        fig.line(x='x', y='y', source=source)
        doc.title = "Tindeq CFT"
        self.btn = Button(label='Waiting for Progressor...')
        button_save = Button(label='Save and back to main menue')
        def mainmenue():
                self.layout.children.pop()
                self.layout.children.pop()
                self.make_document_choice(doc)       
                self.state== IdleState
                doc.remove_periodic_callback(self.calback_update_cft)

                # await self.tindeq.stop_logging_weight()       
                
        button_save.on_click(mainmenue)        
        
        div_instruct = Div(text='<strong>Instructions:</strong> <br>\
                                <ul>\
                                  <li>Turn on tindeq device (small black button)</li>\
                                  <li>Test starts with 10s countdown</li>\
                                  <li>Than pull has hard as you can on 20mm edge for 7s</li>\
                                  <li>Short 3s rest</li>\
                                  <li>Repeat 24x and get ridiculously pumped</li>\
                                </ul>',
                       style={'font-size': '100%', 'color': 'black',                             
                              'text-align': 'left'})
                
        duration_slider = Slider(start=5, end=30, value=24,
                                 step=1, title="Reps")
        self.laps = Div(text=f'Rep {0}/{duration_slider.value}',
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
            self.reps = duration_slider.value
            self.duration = self.reps * 10
            io_loop = tornado.ioloop.IOLoop.current()
            io_loop.add_callback(start_test_cft, self)

        self.btn.on_click(onclick)
        self.btn.disabled=True
        
        widgets = column(div_instruct,duration_slider, self.btn,button_save, self.laps, self.div,self.results_div)
        self.layout = row(widgets, fig)
        doc.add_root(self.layout)
        self.source = source
        self.fig = fig
        self.calback_update_cft = doc.add_periodic_callback(self.update_cft, 50)
        


    def update_cft(self):
        if self.test_done and not self.analysed:
            self.btn.label = 'Test Complete'
            np.savetxt('critical_force_test.txt', np.column_stack((self.x, self.y)))
            x = np.array(self.x)
            y = np.array(self.y)
            
            try:
                results = analyse_data(x, y, 7, 3)
                tmeans, fmeans, e_fmeans, msg, critical_load, load_asymptote, predicted_force = results
                self.cf_peak_load = np.max(fmeans)
                imax=np.argmax(fmeans)
                
                load_asymptote = np.nanmean(fmeans[-5:-1])
                e_load_asymptote = np.nanstd(fmeans[-5:-1]) / np.sum(np.isfinite(fmeans[-5:-1]))
                self.cf_critical_load =load_asymptote   
                self.cf_x = x  
                self.cf_y = y  

                
                msg= '<p>Peak force = {:.2f} +/- {:.2f} kg</p>'.format( fmeans[imax], e_fmeans[imax])
                msg += '<p>Critical force = {:.2f} +/- {:.2f} kg</p>'.format(load_asymptote, e_load_asymptote) 
                self.results_div.text = msg
                # fill_src = ColumnDataSource(dict(x=tmeans, upper=predicted_force,
                #                                  lower=load_asymptote*np.ones_like(tmeans)))
                # self.fig.add_layout(
                #     Band(base='x', lower='lower', upper='upper', source=fill_src, fill_alpha=0.7)
                # )
                self.fig.circle(tmeans, fmeans, color='red', size=5, line_alpha=0)
                esource = ColumnDataSource(dict(x=tmeans, upper=fmeans+e_fmeans, lower=fmeans-e_fmeans))
                self.fig.add_layout(Whisker(source=esource, base='x', upper='upper', lower='lower', level='overlay'))
            except Exception as e  :
                 print(e)
            self.analysed = True
        else:
            if self.tindeq is not None:
                self.btn.disabled=False
                self.btn.label = 'Start Test'
            self.state.update_cft(self)
            self.source.stream({'x': self.xnew, 'y': self.ynew})
            nlaps = self.duration // 10
            self.laps.text = f"Rep {1 + nlaps - self.reps}/{nlaps}"
            self.reset()


async def connect(cft):
    tindeq = TindeqProgressor(cft)
    await tindeq.connect()
    cft.tindeq = tindeq
    await cft.tindeq.soft_tare()
    await asyncio.sleep(1)


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

        cft.state.end(cft)
        await cft.tindeq.start_logging_weight()
        await asyncio.sleep(cft.state.duration)

        print('Test starts!')
        cft.state.end(cft)
        cft.active = True
        await asyncio.sleep(cft.duration)
        await cft.tindeq.stop_logging_weight()
        cft.test_done = True
        await asyncio.sleep(0.5)
        cft.state = IdleState
    except Exception as err:
        print(str(err))
    # finally:
    #     await cft.tindeq.disconnect()
    #     cft.tindeq = None

cft = CFT()
apps = {'/': Application(FunctionHandler(cft.make_gui))}
server = Server(apps, port=5000)
server.start()

if __name__ == "__main__":
    tornado.platform.asyncio.AsyncIOMainLoop().install()
    io_loop = tornado.ioloop.IOLoop.current()
    print('Opening Bokeh application on http://localhost:5006/')
    io_loop.add_callback(server.show, "/")
    io_loop.start()
