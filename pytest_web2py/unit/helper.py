# -*- coding: utf-8 -*-

import logging
import urlparse
from copy import copy

logger = logging.getLogger("pytest_web2py")
logger.addHandler(logging.NullHandler())
logger.setLevel(logging.DEBUG)


def call(w,
         url,
         status=None,
         redirect_url=None,
         next=None,
         controller=None,
         redirect_controller=None,
         next_controller=None,
         render=False,
         view=None,
         check_redirect=True,
         check_status=True,
         **kwargs):
    """ Call controller url with the necessary request information.
        It is expected to raise a HTTP exception, or return a form, or
        return the dictionary returned by the controller function.

        The dictionnary is rendered with response.render except if render is set
        to None.

        If `render` is True,  the function returns a `Storage` with the fieds
        `response` and `html`, the first one being the the dictionary returned
        by the controller functions and the second one being the html as
        rendered.

        If `view` is None, the file used to render HTML id computed from
        controller and function. `view` mays also be a function accepting
        `w` as parameter. For example :
            ```
            call(w, f, render=True, view=lambda: w.response.view)
            ```


        If `redirect_url` url is defined, the call is expected to raise a
        redirection to this URL.
        If redirect_url is set to True, default redirection to `index` is
        expected.
        If `status` is defined it is checked against the redirection status.

        If `check_redirect` is False, redirections is not verified.

        If `check_status` is False, dtatus value is not verified.

        TODO : manage post vars ?

        """
    #TODO update doc

    from gluon.globals import List, Storage
    # decompose URLs
    splitted_url = url.split('?')
    function_part = splitted_url[0]
    if len(splitted_url) > 1:
        vars_part = splitted_url[1]
    else:
        vars_part = ""

    dget = urlparse.parse_qs(vars_part, keep_blank_values=1)  # Ref: https://docs.python.org/2/library/cgi.html#cgi.parse_qs
    get_vars = Storage(dget)
    for (key, value) in get_vars.iteritems():
        if isinstance(value, list) and len(value) == 1:
            get_vars[key] = value[0]

    args = function_part.split('/')
    function = args[0]
    w.request.vars.clear()
    w.request.get_vars.clear()
    w.request.function = function
    w.request.args = List(args[1:])
    w.request._vars.update(get_vars)
    w.request._vars.update(w.request.post_vars)
    w.request._get_vars = get_vars
    logger.debug("args = %s", w.request.args)
    logger.debug("vars = %s", w.request.vars)
    logger.debug("get_vars = %s", w.request.get_vars)
    r_url = redirect_url
    controller = controller or w.request.controller
    redirect_controller = redirect_controller or controller
    if r_url:
        if r_url is True:
            r_url = '/%s/%s/index' % (w.request.application, redirect_controller or controller)
        elif not w.request.application in redirect_url:
            r_url = '/%s/%s/%s' % (w.request.application, redirect_controller or controller,
                                 redirect_url)
    else:
        r_url = ''
    if next:
        if next == True:
            r_url += '?_next=/%s/%s/%s' % (w.request.application,
                                           next_controller or controller,
                                           function)
            r = [r_url]
            r.extend(args[1:])
            r_url = '/'.join(r)
        else:
            r_url += '?_next=%s' % next
    #if w.request.args:
    #r_url += "/" + '/'.join(w.request.args)
    try:
        logger.debug("→ Calling %s in %s", url, controller)
        from gluon.compileapp import run_controller_in
        resp = w.run(function, controller)
        logger.debug("Flash s:%s r:%s", w.session.flash, w.response.flash)
        if check_redirect:
            assert r_url == '', ('Expected redirection to %s didn\'t occurred' % r_url)
        res = resp
        if render is not None:
            env = copy(w)
            env.update(resp)
            if not view:
                view = '%s/%s.html' % (controller, function)
            elif callable(view):
                view = view(w)
            logging.debug("Render with %s", view)
            html = w.response.render(view, env)
            if render:
                from gluon.globals import Storage
                res = Storage()
                res.response = resp
                res.html = html
        return res

    except w.HTTP as e:
        logger.debug("Flash s:%s r:%s", w.session.flash, w.response.flash)
        logger.debug("Exception: %s", e)
        if r_url:
            status = status or 303
        location = e.headers.get('Location', None) \
            or e.headers.get('web2py-redirect-location', None)\
            or e.headers.get('web2py-component-command', None) or None
        if location != r_url:
            logger.debug("redirect to: %s\nUser '%s'. Logged:%s", location,
                         w.auth.user, w.auth.is_logged_in())
        if check_status:
            assert e.status == status,\
                "status %s expected (%s found) for url '%s'" % ( status,
                                                                e.status, url)

        if check_redirect:
            assert location == r_url, ("Wrong redirection url on %s() : %s "
                                     "(%s expected)" % (function, location, r_url
                                                        or None))
        if check_redirect and not r_url:
            raise e
        else:
            return e


def form_post(w,
              function,
              data,
              args=None,
              status=None,
              redirect_url=None,
              next=None,
              crud_db=None,
              crud_record_id=None,
              controller=None,
              redirect_controller=None,
              next_controller=None,
              formname=None,
              formkey=None,
              check_redirect=True,
              check_status=True,
              **kwargs):
    """ Fill the form returned by `callable` with `data` dictionary and post it
    For crud form there are two supplementary parameters
    `crud_action` shall be one of the CRUD action ('create', 'read', 'update',…),
    `crud_record_id` if the id of the record concerned by the action if any.
    """
    logger.debug("→ form_post data: %s", data)
    if crud_db:
        _formname = "%s/%s" % (crud_db, crud_record_id)
    else:
        _formname = formname or function.split('/')[-1]

    _formkey = _formname
    hidden = dict(_formkey=_formname, _formname=_formname)
    logger.debug("formname: %s formkey: %s", _formname, _formkey)
    w.request.post_vars.clear()
    w.request.vars.clear()
    if data:
        w.request.post_vars.update(data)
        w.request.vars.update(data)
    w.request.post_vars.update(hidden)
    w.request.vars.update(hidden)
    for k in [k for k in w.session if "_formkey[" in k]:
        del w.session[k]

    w.session["_formkey[%s]" % _formname] = [_formkey]
    res = call(
        w,
        function,
        redirect_url=redirect_url,
        status=status,
        next=next,
        controller=controller,
        redirect_controller=redirect_controller,
        next_controller=next_controller,
        check_redirect=check_redirect,
        check_status=check_status,
        **kwargs)
    return res
