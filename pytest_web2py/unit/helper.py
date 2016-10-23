# -*- coding: utf-8 -*-

import logging
from copy import copy

logger = logging.getLogger("pytest_web2py")
logger.addHandler(logging.NullHandler())
logger.setLevel(logging.DEBUG)


def call(w,
         function_name,
         status=None,
         redirect_url=None,
         next=None,
         controller=None,
         redirect_controller=None,
         next_controller=None,
         render=False,
         view=None):
    """ Call controller function with the necessary request information.
        It expects `function` to raise a HTTP exception, or return a form, or
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

        """
    #TODO update doc

    from gluon.globals import List
    args = function_name.split('/')
    function = args[0]
    w.request.function = function
    w.request.args = List(args[1:])
    logger.debug("args = %s", w.request.args)
    url = redirect_url
    controller = controller or w.request.controller
    redirect_controller = redirect_controller or controller

    if url:
        if url is True:
            url = '/%s/%s/index' % (w.request.application, redirect_controller
                                    or controller)
        elif not w.request.application in redirect_url:
            url = '/%s/%s/%s' % (w.request.application, redirect_controller or
                                 controller, redirect_url)
    else:
        url = ''

    if next:
        if next == True:
            url += '?_next=/%s/%s/%s' % (
                w.request.application, next_controller or controller, function)
            r = [url]
            r.extend(args[1:])
            url = '/'.join(r)
        else:
            url += '?_next=%s' % next

    try:
        logger.debug("→ Calling %s in %s", function_name, controller)
        from gluon.compileapp import run_controller_in
        resp = w.run(function, controller)
        logger.debug("Flash s:%s r:%s", w.session.flash, w.response.flash)
        assert url == '', ('Expected redirection to %s didn\'t occurred' % url)
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
        if url:
            status = status or 303
        location = e.headers.get('Location', None) \
            or e.headers.get('web2py-redirect-location', None)\
            or e.headers.get('web2py-component-command', None) or None
        if location != url:
            logger.debug("redirect to: %s\nUser '%s'. Logged:%s", location,
                         w.auth.user, w.auth.is_logged_in())
        assert e.status == status, "status %s expected (%s found) for url '%s'" % (
            status, e.status, url)

        assert location == url, ("Wrong redirection url on %s() : %s "
                                 "(%s expected)" %
                                 (function, location, url or None))
        if not url:
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
              formkey=None):
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

    if data:
        w.request.post_vars.update(data)

    w.request.post_vars.update(hidden)

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
        next_controller=next_controller)
    return res
